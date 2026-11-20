import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseRead, CourseCreate
from app.models.lesson import Lesson


router = APIRouter(prefix="/courses", tags=["Курсы"])
BASE_DIR = Path(__file__).resolve().parents[2]


async def save_course_image(image: UploadFile | None) -> str | None:
    if image is None or not image.filename:
        return None

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    extension = allowed_types.get(image.content_type or "")
    if extension is None:
        raise HTTPException(400, "Разрешены только JPG, PNG и WEBP")

    content = await image.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "Изображение не должно превышать 5 МБ")

    upload_dir = BASE_DIR / "static" / "uploads" / "courses"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}{extension}"
    (upload_dir / filename).write_bytes(content)
    return f"/static/uploads/courses/{filename}"


@router.post("/create", response_model=CourseRead)
def create_course(
    data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = Course(
        user_id=current_user.id,
        title=data.title,
        description=data.description,
        price=data.price
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.post("/create-with-image", response_model=CourseRead)
async def create_course_with_image(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(0),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if price < 0:
        raise HTTPException(400, "Цена не может быть отрицательной")

    image_url = await save_course_image(image)
    course = Course(
        user_id=current_user.id,
        title=title,
        description=description,
        price=price,
        image_url=image_url,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/all", response_model=list[CourseRead])
def get_courses(db: Session = Depends(get_db)):
    return db.query(Course).order_by(Course.id.desc()).all()


@router.get("/{course_id}", response_model=CourseRead)
def get_course_by_id(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(404, "Курс не найден")
    return course


@router.delete("/{course_id}/delete")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    if course is None:
        raise HTTPException(404, "Курс не найден")

    lesson = db.query(Lesson).filter(Lesson.course_id == course_id).first()
    if lesson is not None:
        raise HTTPException(400, "Сначала удалите уроки курса")

    db.delete(course)
    db.commit()
    return {"message": "Курс успешно удалён"}


@router.put("/{course_id}", response_model=CourseRead)
def update_course(
    course_id: int,
    data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    if course is None:
        raise HTTPException(404, "Курс не найден")

    course.title = data.title
    course.description = data.description
    course.price = data.price
    db.commit()
    db.refresh(course)
    return course
