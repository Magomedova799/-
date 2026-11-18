import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.lesson import Lesson
from app.models.course import Course
from app.models.user import User
from app.schemas.lesson import LessonRead


router = APIRouter(prefix="/lessons", tags=["Уроки"])


@router.post("/create", response_model=LessonRead)
async def create_lessons(
    course_id: int = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    position: int = Form(...),
    video_url: str | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Курс не найден или у вас нет доступа"
        )

    image_url = None

    if image is not None:
        allowed_types = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp"
        }

        if image.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Разрешены только JPG, PNG и WEBP"
            )

        extension = allowed_types[image.content_type]
        filename = f"{uuid.uuid4()}{extension}"

        upload_dir = Path("static/uploads/lessons/photos")
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / filename
        file_path.write_bytes(await image.read())

        image_url = f"/static/uploads/lessons/photos/{filename}"

    lesson = Lesson(
        course_id=course_id,
        title=title,
        content=content,
        position=position,
        image_url=image_url,
        video_url=video_url
    )

    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return lesson


@router.get("/all", response_model=list[LessonRead])
def get_lessons(db: Session = Depends(get_db)):
    return db.query(Lesson).order_by(Lesson.id.desc()).all()

@router.get("/{lesson_id}", response_model=LessonRead)
def get_lesson_by_id(
    lesson_id: int,
    db: Session = Depends(get_db)
):
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id
    ).first()

    if lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")

    return lesson


@router.get("/course/{course_id}", response_model=list[LessonRead])
def get_lessons_by_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    lessons = db.query(Lesson).filter(
        Lesson.course_id == course_id
    ).order_by(Lesson.position.asc()).all()

    return lessons


@router.delete("/{lesson_id}/delete")
def delete_lesson(lesson_id: int,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id,
        Lesson.course_id.in_(
            db.query(Course.id).filter(
                Course.user_id == current_user.id
            )
        )
    ).first()

    if lesson is None:
        raise HTTPException(
            status_code=404,
            detail="Урок не найден"
        )

    db.delete(lesson)
    db.commit()

    return {"message": "Урок удален"}
