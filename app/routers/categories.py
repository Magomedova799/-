from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, get_admin_user
from app.models.category import Category
from app.models.user import User
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


@router.get("/all", response_model=list[CategoryRead])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.id).all()
    return categories

@router.put("/{category_id}/editing", response_model=CategoryRead)
def update_category(
    category_id: int,
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(
        category.id == category_id,
    ).first()

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Категория не найдена"
        )

    category.name = data.name
    category.description = data.description

    db.commit()
    db.refresh(category)

    return category



@router.delete("/{category_id}/delete")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    category = db.query(Category).filter(
        Category.id == category_id
    ).first()

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Категория не найдена"
        )

    db.delete(category)
    db.commit()

    return {"message": "Категория удалена"}