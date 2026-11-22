from fastapi import APIRouter, Depends, HTTPException,Request
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.article import Article
from app.models.user import User
from app.schemas.article import ArticleCreate, ArticleRead
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi import Form
from fastapi.responses import RedirectResponse
from app.dependencies import get_optional_user
from app.models.like import Like
from app.models.comment import Comment
from app.models.category import Category


router = APIRouter(
    prefix="/articles",
    tags=["Статьи"]
)

templates = Jinja2Templates(directory="templates")


@router.get("/create-page")
def article_create_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="article_create.html",
        context={}
    )



@router.get("/create-form")
def create_article_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    categories = db.query(Category).order_by(Category.name).all()

    return templates.TemplateResponse(
        "create_article.html",
        {
            "request": request,
            "user": current_user,
            "categories": categories
        }
    )


@router.get("/all", response_model=list[ArticleRead])
def get_articles(db: Session = Depends(get_db)):
    return db.query(Article).order_by(Article.id.desc()).all()


@router.get("/article/{article_id}")
def article_page(
    article_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user)
):
    article = db.query(Article).filter(
        Article.id == article_id
    ).first()

    if not article:
        raise HTTPException(
            status_code=404,
            detail="Статья не найдена"
        )

    author = db.query(User).filter(
        User.id == article.user_id
    ).first()

    likes_count = db.query(Like).filter(
        Like.article_id == article_id
    ).count()

    is_liked = False

    if current_user:
        is_liked = db.query(Like).filter(
            Like.article_id == article_id,
            Like.user_id == current_user.id
        ).first() is not None

    comments = (
        db.query(Comment, User.username)
        .join(User, Comment.user_id == User.id)
        .filter(Comment.article_id == article_id)
        .order_by(Comment.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="article_detail.html",
        context={
            "article": article,
            "author": author,
            "user": current_user,
            "current_user": current_user,
            "likes_count": likes_count,
            "is_liked": is_liked,
            "comments": comments
        }
    )

@router.post("/article/{article_id}/like")
def toggle_article_like(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = db.query(Article).filter(
        Article.id == article_id
    ).first()

    if article is None:
        raise HTTPException(404, "Статья не найдена")

    like = db.query(Like).filter(
        Like.article_id == article_id,
        Like.user_id == current_user.id
    ).first()

    if like:
        db.delete(like)
    else:
        db.add(Like(
            user_id=current_user.id,
            article_id=article_id
        ))

    db.commit()

    return RedirectResponse(
        url=f"/articles/article/{article_id}",
        status_code=303
    )


@router.post("/article/{article_id}/comment")
def add_article_comment(
    article_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = db.query(Article).filter(
        Article.id == article_id
    ).first()

    if article is None:
        raise HTTPException(404, "Статья не найдена")

    content = content.strip()

    if not content or len(content) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Комментарий должен содержать от 1 до 2000 символов"
        )

    comment = Comment(
        user_id=current_user.id,
        article_id=article_id,
        content=content
    )

    db.add(comment)
    db.commit()

    return RedirectResponse(
        url=f"/articles/article/{article_id}",
        status_code=303
    )


@router.get("/{article_id}/edit")
def article_edit_page(
    article_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.user_id == current_user.id
    ).first()

    if article is None:
        raise HTTPException(404, "Статья не найдена")

    return templates.TemplateResponse(
        request=request,
        name="article_edit.html",
        context={
            "article": article
        }
    )


@router.post("/{article_id}/edit")
def update_article_form(
    article_id: int,
    title: str = Form(...),
    content: str = Form(...),
    category_id: int | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.user_id == current_user.id
    ).first()

    if article is None:
        raise HTTPException(404, "Статья не найдена")

    article.title = title
    article.content = content
    article.category_id = category_id

    db.commit()

    return RedirectResponse(
        url=f"/articles/article/{article_id}",
        status_code=303
    )

@router.post("/{article_id}/delete")
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

    return RedirectResponse(
        url="/",
        status_code=303
    )
