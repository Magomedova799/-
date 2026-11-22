from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseRead, CourseCreate
from app.models.lesson import Lesson
from fastapi.templating import Jinja2Templates
from app.dependencies import get_optional_user
from app.models.lesson_test import LessonTest
from app.models.assignment import Assignment
from app.models.subscription import Subscription
from fastapi import Form
from fastapi.responses import RedirectResponse
from decimal import Decimal

router = APIRouter(prefix="/courses", tags=["Курсы"])
templates = Jinja2Templates(directory="templates")


@router.get("/create-page")
def course_create_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        request=request,
        name="course_create.html",
        context={
            "user": current_user
        }
    )

@router.post("/create-form")
def create_course_form(
    title: str = Form(...),
    description: str = Form(...),
    price: Decimal = Form(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = Course(
        user_id=current_user.id,
        title=title,
        description=description,
        price=price
    )

    db.add(course)
    db.commit()

    return RedirectResponse(
        url="/",
        status_code=303
    )


@router.get("/all", response_model=list[CourseRead])
def get_courses(db: Session = Depends(get_db)):
    return db.query(Course).order_by(Course.id.desc()).all()


@router.get("/page/{course_id}")
def course_page(
    course_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user)
):
    course = db.query(Course).filter(Course.id == course_id).first()

    if course is None:
        raise HTTPException(status_code=404, detail="Курс не найден")

    author = db.query(User).filter(User.id == course.user_id).first()

    # Получаем уроки курса по порядку
    lessons = (
        db.query(Lesson)
        .filter(Lesson.course_id == course_id)
        .order_by(Lesson.position)
        .all()
    )

    # Проверяем, записан ли пользователь на курс
    is_subscribed = False

    if current_user:
        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == current_user.id,
                Subscription.course_id == course_id
            )
            .first()
        )

        is_subscribed = subscription is not None

    # Для каждого урока получаем тесты и задания
    lessons_data = []

    for lesson in lessons:
        tests = (
            db.query(LessonTest)
            .filter(LessonTest.lesson_id == lesson.id)
            .all()
        )

        assignments = (
            db.query(Assignment)
            .filter(Assignment.lesson_id == lesson.id)
            .order_by(Assignment.position)
            .all()
        )

        lessons_data.append({
            "lesson": lesson,
            "tests": tests,
            "assignments": assignments
        })

    return templates.TemplateResponse(
        request=request,
        name="course_detail.html",
        context={
            "course": course,
            "author": author,
            "lessons_data": lessons_data,
            "current_user": current_user,
            "is_subscribed": is_subscribed
        }
    )

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
        raise HTTPException(
            status_code=404,
            detail="Курс не найден"
        )

    lessons = db.query(Lesson).filter(
        Lesson.course_id == course_id
    ).first()

    if lessons is not None:
        raise HTTPException(
            status_code=400,
            detail="Сначала удалите уроки курса"
        )

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

    
    