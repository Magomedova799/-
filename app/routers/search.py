from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.course import Course
from app.models.article import Article
from app.models.project import Project
from app.models.poll import Poll

router = APIRouter(prefix="/search", tags=["Поиск"])


@router.get("/")
def search_materials(
    q: str = Query(default="", max_length=200),
    content_type: str = Query(default="all"),
    category_id: int | None = None,
    db: Session = Depends(get_db),
):
    term = q.strip()
    result = []

    def add(items, kind):
        for item in items:
            row = {
                "id": item.id,
                "type": kind,
                "title": getattr(item, "title", None) or getattr(item, "question", ""),
                "description": getattr(item, "description", None) or getattr(item, "content", None) or "",
                "created_at": item.created_at,
                "user_id": item.user_id,
                "image_url": getattr(item, "image_url", None),
                "category_id": getattr(item, "category_id", None),
            }
            if kind == "Курс":
                row["price"] = str(item.price)
            elif kind == "Проект":
                row["technologies"] = item.technologies
            elif kind == "Опрос":
                row.update({
                    "options": item.options,
                    "votes": item.votes,
                    "is_active": item.is_active,
                })
            result.append(row)

    if content_type in ("all", "courses"):
        query = db.query(Course)
        if term:
            query = query.filter(or_(Course.title.ilike(f"%{term}%"), Course.description.ilike(f"%{term}%")))
        add(query.order_by(Course.created_at.desc()).limit(100).all(), "Курс")

    if content_type in ("all", "articles"):
        query = db.query(Article)
        if term:
            query = query.filter(or_(Article.title.ilike(f"%{term}%"), Article.content.ilike(f"%{term}%")))
        if category_id:
            query = query.filter(Article.category_id == category_id)
        add(query.order_by(Article.created_at.desc()).limit(100).all(), "Статья")

    if content_type in ("all", "projects"):
        query = db.query(Project)
        if term:
            query = query.filter(or_(Project.title.ilike(f"%{term}%"), Project.description.ilike(f"%{term}%"), Project.technologies.ilike(f"%{term}%")))
        if category_id:
            query = query.filter(Project.category_id == category_id)
        add(query.order_by(Project.created_at.desc()).limit(100).all(), "Проект")

    if content_type in ("all", "polls"):
        query = db.query(Poll)
        if term:
            query = query.filter(Poll.question.ilike(f"%{term}%"))
        add(query.order_by(Poll.created_at.desc()).limit(100).all(), "Опрос")

    result.sort(key=lambda row: row["created_at"], reverse=True)
    return result
