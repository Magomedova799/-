
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.course import Course
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

    likes_count = (
        db.query(Like)
        .filter(
            or_(
                Like.course_id.in_(
                    db.query(Course.id).filter(Course.user_id == user.id)
                ),
                Like.project_id.in_(
                    db.query(Project.id).filter(Project.user_id == user.id)
                ),
                Like.article_id.in_(
                    db.query(Article.id).filter(Article.user_id == user.id)
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
            "projects": projects,
            "articles": articles,
            "author_subscriptions": author_subscriptions,
            "course_subscriptions": course_subscriptions,
            "publications_count": len(courses) + len(projects) + len(articles),
            "subscriptions_count": len(author_subscriptions) + len(course_subscriptions),
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
    avatar_url: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    username = username.strip()

    existing_user = db.query(User).filter(
        User.username == username,
        User.id != user.id
    ).first()

    if existing_user:
        return RedirectResponse("/profile/edit?error=1", status_code=303)

    user.username = username
    user.bio = bio.strip() or None
    user.avatar_url = avatar_url.strip() or None

    db.commit()

    return RedirectResponse("/profile", status_code=303)

