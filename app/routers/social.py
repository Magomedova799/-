from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.subscription import Subscription
from app.models.like import Like
from app.models.comment import Comment
from app.models.user import User
from app.models.course import Course
from app.models.article import Article
from app.models.project import Project


router = APIRouter(tags=["Подписки, лайки и комментарии"])


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

def get_subscription_field(target_type: str):
    if target_type == "authors":
        return "author_id", User
    if target_type == "courses":
        return "course_id", Course

    raise HTTPException(status_code=400, detail="Неверный тип подписки")

def get_content_field(target_type: str):
    if target_type == "courses":
        return "course_id", Course
    if target_type == "articles":
        return "article_id", Article
    if target_type == "projects":
        return "project_id", Project

    raise HTTPException(status_code=400, detail="Неверный тип объекта")


# ---------------- ПОДПИСКИ ----------------

@router.post("/subscriptions/{target_type}/{target_id}")
def subscribe(
    target_type: str,
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    field, model = get_subscription_field(target_type)

    target = db.query(model).filter(model.id == target_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="Объект не найден")

    if target_type == "authors" and target_id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя подписаться на себя")

    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        getattr(Subscription, field) == target_id
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Вы уже подписаны")

    subscription = Subscription(
        user_id=current_user.id,
        **{field: target_id}
    )

    db.add(subscription)
    db.commit()

    return {"message": "Подписка оформлена"}


@router.delete("/subscriptions/{target_type}/{target_id}")
def unsubscribe(
    target_type: str,
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    field, model = get_subscription_field(target_type)

    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        getattr(Subscription, field) == target_id
    ).first()

    if subscription is None:
        raise HTTPException(status_code=404, detail="Подписка не найдена")

    db.delete(subscription)
    db.commit()

    return {"message": "Вы отписались"}


@router.get("/subscriptions/my")
def get_my_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).all()

    return [
        {
            "id": item.id,
            "author_id": item.author_id,
            "course_id": item.course_id,
            "created_at": item.created_at
        }
        for item in subscriptions
    ]


# ---------------- ЛАЙКИ ----------------

@router.post("/likes/{target_type}/{target_id}")
def add_like(
    target_type: str,
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    field, model = get_content_field(target_type)

    target = db.query(model).filter(model.id == target_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="Объект не найден")

    existing = db.query(Like).filter(
        Like.user_id == current_user.id,
        getattr(Like, field) == target_id
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Вы уже поставили лайк")

    like = Like(
        user_id=current_user.id,
        **{field: target_id}
    )

    db.add(like)
    db.commit()

    return {"message": "Лайк поставлен"}


@router.delete("/likes/{target_type}/{target_id}")
def remove_like(
    target_type: str,
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    field, model = get_content_field(target_type)

    like = db.query(Like).filter(
        Like.user_id == current_user.id,
        getattr(Like, field) == target_id
    ).first()

    if like is None:
        raise HTTPException(status_code=404, detail="Лайк не найден")

    db.delete(like)
    db.commit()

    return {"message": "Лайк удалён"}


@router.get("/likes/my")
def get_my_likes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    likes = db.query(Like).filter(
        Like.user_id == current_user.id
    ).all()

    return [
        {
            "id": item.id,
            "course_id": item.course_id,
            "article_id": item.article_id,
            "project_id": item.project_id,
            "created_at": item.created_at
        }
        for item in likes
    ]


# ---------------- КОММЕНТАРИИ ----------------

@router.post("/comments/{target_type}/{target_id}")
def add_comment(
    target_type: str,
    target_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    field, model = get_content_field(target_type)

    target = db.query(model).filter(model.id == target_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="Объект не найден")

    comment = Comment(
        user_id=current_user.id,
        content=data.content,
        **{field: target_id}
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {
        "message": "Комментарий добавлен",
        "id": comment.id,
        "content": comment.content
    }


@router.get("/comments/{target_type}/{target_id}")
def get_comments(
    target_type: str,
    target_id: int,
    db: Session = Depends(get_db)
):
    field, model = get_content_field(target_type)

    target = db.query(model).filter(model.id == target_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="Объект не найден")

    comments = db.query(Comment, User.username).join(
        User, Comment.user_id == User.id
    ).filter(
        getattr(Comment, field) == target_id
    ).order_by(Comment.created_at.desc()).all()

    return [
        {
            "id": comment.id,
            "username": username,
            "content": comment.content,
            "created_at": comment.created_at
        }
        for comment, username in comments
    ]


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.user_id == current_user.id
    ).first()

    if comment is None:
        raise HTTPException(
            status_code=404,
            detail="Комментарий не найден"
        )

    db.delete(comment)
    db.commit()

    return {"message": "Комментарий удалён"}