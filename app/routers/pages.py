from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter,Depends,Form, Request,HTTPException,UploadFile,File

from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.project import Project
from app.models.article import Article
from app.models.like import Like
from app.models.subscription import Subscription


router = APIRouter(tags=["HTML страницы"])
templates = Jinja2Templates(directory="templates")


@router.get("/profile")
def profile(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    courses = db.query(Course).filter(
        Course.user_id == user.id
    ).all()

    course_lessons = {}

    for course in courses:
        course_lessons[course.id] = (
            db.query(Lesson)
            .filter(Lesson.course_id == course.id)
            .order_by(Lesson.position.asc())
            .all()
        )

    projects = db.query(Project).filter(
        Project.user_id == user.id
    ).all()

    articles = db.query(Article).filter(
        Article.user_id == user.id
    ).all()

    author_subscriptions = (
        db.query(Subscription, User)
        .join(User, Subscription.author_id == User.id)
        .filter(Subscription.user_id == user.id)
        .all()
    )

    course_subscriptions = (
        db.query(Subscription, Course)
        .join(Course, Subscription.course_id == Course.id)
        .filter(Subscription.user_id == user.id)
        .all()
    )

    liked_courses = (
        db.query(Course)
        .join(Like, Like.course_id == Course.id)
        .filter(Like.user_id == user.id)
        .all()
    )

    liked_projects = (
        db.query(Project)
        .join(Like, Like.project_id == Project.id)
        .filter(Like.user_id == user.id)
        .all()
    )

    liked_articles = (
        db.query(Article)
        .join(Like, Like.article_id == Article.id)
        .filter(Like.user_id == user.id)
        .all()
    )

    likes_count = (
        db.query(Like)
        .filter(
            or_(
                Like.course_id.in_(
                    db.query(Course.id).filter(
                        Course.user_id == user.id
                    )
                ),
                Like.project_id.in_(
                    db.query(Project.id).filter(
                        Project.user_id == user.id
                    )
                ),
                Like.article_id.in_(
                    db.query(Article.id).filter(
                        Article.user_id == user.id
                    )
                )
            )
        )
        .count()
    )

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "courses": courses,
            "course_lessons": course_lessons,
            "projects": projects,
            "articles": articles,
            "author_subscriptions": author_subscriptions,
            "course_subscriptions": course_subscriptions,
            "liked_courses": liked_courses,
            "liked_projects": liked_projects,
            "liked_articles": liked_articles,
            "publications_count": (
                len(courses) + len(projects) + len(articles)
            ),
            "subscriptions_count": (
                len(author_subscriptions) + len(course_subscriptions)
            ),
            "likes_count": likes_count
        }
    )


@router.get("/profile/edit")
def edit_profile_page(
    request: Request,
    user: User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        request=request,
        name="edit_profile.html",
        context={"user": user}
    )


@router.post("/profile/edit")
def edit_profile(
    username: str = Form(...),
    bio: str = Form(""),
    avatar: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    username = username.strip()

    existing_user = db.query(User).filter(
        User.username == username,
        User.id != user.id
    ).first()

    if existing_user:
        return RedirectResponse(
            "/profile/edit?error=1",
            status_code=303
        )

    user.username = username
    user.bio = bio.strip() or None

    if avatar and avatar.filename:

        allowed_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".gif"
        }

        extension = Path(avatar.filename).suffix.lower()

        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail="Разрешены только JPG, JPEG, PNG, WEBP и GIF"
            )

        file_content = avatar.file.read()

        if len(file_content) > 20 * 1024 * 1024:
             raise HTTPException(
                status_code=400,
                detail="Размер аватара не должен превышать 20 МБ"
    )

        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="Выбран пустой файл"
            )

        upload_dir = Path("static") / "uploads" / "ava"
        upload_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid4().hex}{extension}"

        file_path = upload_dir / filename
        file_path.write_bytes(file_content)

        user.avatar_url = f"/static/uploads/ava/{filename}"

    db.commit()

    return RedirectResponse(
        "/profile",
        status_code=303
    )

@router.get("/users/{user_id}")
def public_profile(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile_user = db.query(User).filter(
        User.id == user_id
    ).first()

    if profile_user is None:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )

    if profile_user.id == current_user.id:
        return RedirectResponse(
            "/profile",
            status_code=303
        )

    courses = db.query(Course).filter(
        Course.user_id == profile_user.id
    ).all()

    projects = db.query(Project).filter(
        Project.user_id == profile_user.id
    ).all()

    articles = db.query(Article).filter(
        Article.user_id == profile_user.id
    ).all()

    followers_count = db.query(Subscription).filter(
        Subscription.author_id == profile_user.id
    ).count()

    subscriptions_count = db.query(Subscription).filter(
        Subscription.user_id == profile_user.id
    ).count()

    is_subscribed = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.author_id == profile_user.id
    ).first() is not None

    return templates.TemplateResponse(
        request=request,
        name="public_profile.html",
        context={
            "user": profile_user,
            "courses": courses,
            "projects": projects,
            "articles": articles,
            "followers_count": followers_count,
            "subscriptions_count": subscriptions_count,
            "publications_count": (
                len(courses) + len(projects) + len(articles)
            ),
            "is_subscribed": is_subscribed
        }
    )

@router.post("/users/{user_id}/subscribe")
def subscribe_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target = db.query(User).filter(
        User.id == user_id
    ).first()

    if target is None:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )

    if target.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Нельзя подписаться на себя"
        )

    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.author_id == target.id
    ).first()

    if not existing:
        db.add(
            Subscription(
                user_id=current_user.id,
                author_id=target.id
            )
        )
        db.commit()

    return RedirectResponse(
        url=f"/users/{user_id}",
        status_code=303
    )

@router.post("/users/{user_id}/unsubscribe")
def unsubscribe_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.author_id == user_id
    ).first()

    if subscription:
        db.delete(subscription)
        db.commit()

    return RedirectResponse(
        url=f"/users/{user_id}",
        status_code=303
    )
