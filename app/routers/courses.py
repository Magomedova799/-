from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseRead, CourseCreate


router = APIRouter(prefix="/courses", tags=["Курсы"])


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


@router.get("/all", response_model=list[CourseRead])
def get_courses(db: Session = Depends(get_db)):
    return db.query(Course).order_by(Course.id.desc()).all()


@router.get("/{course_id}", response_model=CourseRead)
def get_course_by_id(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Курс не найден"
        )

    return course

@router.delete("/{course_id}/delete")
def delete_course(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    course = db.query(Course).filter(
        Course.id == course_id,
        course.user_id == current_user.id
    ).filter()

    if course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    db.delete(course)
    db.commit()

    return {"message": "Курс удален"}
    
    