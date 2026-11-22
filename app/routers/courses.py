
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from decimal import Decimal

from app.dependencies import get_db, get_current_user, get_optional_user

from app.models.course import Course
from app.models.user import User
from app.models.lesson import Lesson
from app.models.lesson_test import LessonTest
from app.models.assignment import Assignment
from app.models.subscription import Subscription
from app.models.like import Like
from app.models.comment import Comment

from app.schemas.course import CourseRead, CourseCreate


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
    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Курс не найден"
        )

    author = db.query(User).filter(
        User.id == course.user_id
    ).first()

    lessons = (
        db.query(Lesson)
        .filter(Lesson.course_id == course_id)
        .order_by(Lesson.position)
        .all()
    )

    is_subscribed = False

    if current_user:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.course_id == course_id
        ).first()

        is_subscribed = subscription is not None

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

    likes_count = db.query(Like).filter(
        Like.course_id == course_id
    ).count()


    is_liked = False

    if current_user:
        is_liked = db.query(Like).filter(
            Like.course_id == course_id,
            Like.user_id == current_user.id
        ).first() is not None

    comments = (
        db.query(Comment, User.username)
        .join(User, Comment.user_id == User.id)
        .filter(Comment.course_id == course_id)
        .order_by(Comment.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="course_detail.html",
        context={
            "course": course,
            "author": author,
            "lessons": lessons,
            "lessons_data": lessons_data,
            "current_user": current_user,
            "is_subscribed": is_subscribed,
            "likes_count": likes_count,
            "is_liked": is_liked,
            "comments": comments
        }
    )



@router.post("/page/{course_id}/like")
def toggle_course_like(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Курс не найден"
        )

    like = db.query(Like).filter(
        Like.course_id == course_id,
        Like.user_id == current_user.id
    ).first()

    if like:
        db.delete(like)
    else:
        db.add(Like(
            user_id=current_user.id,
            course_id=course_id
        ))

    db.commit()

    return RedirectResponse(
        url=f"/courses/page/{course_id}",
        status_code=303
    )


@router.post("/page/{course_id}/comment")
def add_course_comment(
    course_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Курс не найден"
        )

    content = content.strip()

    if not content or len(content) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Комментарий должен содержать от 1 до 2000 символов"
        )

    comment = Comment(
        user_id=current_user.id,
        course_id=course_id,
        content=content
    )

    db.add(comment)
    db.commit()

    return RedirectResponse(
        url=f"/courses/page/{course_id}",
        status_code=303
    )



@router.get("/{course_id}/edit")
def edit_course_page(
    course_id: int,
    request: Request,
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

    return templates.TemplateResponse(
        request=request,
        name="course_edit.html",
        context={
            "user": current_user,
            "course": course
        }
    )


@router.post("/{course_id}/edit")
def edit_course_form(
    course_id: int,
    title: str = Form(...),
    description: str = Form(...),
    price: Decimal = Form(0),
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

    course.title = title
    course.description = description
    course.price = price

    db.commit()

    return RedirectResponse(
        url="/profile",
        status_code=303
    )


@router.post("/{course_id}/delete")
def delete_course_form(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Курс не найден"
        )

    try:
        db.delete(course)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return RedirectResponse(
        url="/dashboard",
        status_code=303
    )



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
        raise HTTPException(
            status_code=404,
            detail="Курс не найден"
        )

    course.title = data.title
    course.description = data.description
    course.price = data.price

    db.commit()
    db.refresh(course)

    return course
