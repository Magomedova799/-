
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.article import Article
from app.models.user import User
from app.schemas.article import ArticleCreate, ArticleRead


router = APIRouter(
    prefix="/articles",
    tags=["Статьи"]
)

@router.post("/create", response_model=ArticleRead)
def create_article(
    data: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = Article(
        user_id=current_user.id,
        title=data.title,
        content=data.content,
        category_id=data.category_id
    )

    db.add(article)
    db.commit()
    db.refresh(article)

    return article


@router.get("/all", response_model=list[ArticleRead])
def get_articles(db: Session = Depends(get_db)):
    return db.query(Article).order_by(Article.id.desc()).all()


@router.get("/{article_id}", response_model=ArticleRead)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(
        Article.id == article_id
    ).first()

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Статья не найдена"
        )

    return article


@router.put("/{article_id}/editing", response_model=ArticleRead)
def update_article(
    article_id: int,
    data: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.user_id == current_user.id
    ).first()

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Статья не найдена"
        )

    article.title = data.title
    article.content = data.content
    article.category_id = data.category_id

    db.commit()
    db.refresh(article)

    return article



@router.delete("/{article_id}/delete")
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.user_id == current_user.id
    ).first()

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Статья не найдена"
        )

    db.delete(article)
    db.commit()

    return {"message": "Статья успешно удалена"}
