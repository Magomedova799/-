from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryRead


router = APIRouter(
    prefix="/categories",
    tags=["Категории"]
)


@router.post("/create", response_model=CategoryRead)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db)
):
    existing_category = db.query(Category).filter(
        Category.name == data.name
    ).first()

    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Такая категория уже существует"
        )

    category = Category(
        name=data.name,
        description=data.description
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.get("/", response_model=list[CategoryRead])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.id).all()
    return categories