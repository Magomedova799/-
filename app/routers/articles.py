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


@router.post("/create-form")
def create_article_form(
    title: str = Form(...),
    content: str = Form(...),
    category_id: int | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = Article(
        user_id=current_user.id,
        title=title,
        content=content,
        category_id=category_id
    )

    db.add(article)
    db.commit()

    return RedirectResponse(
        url="/",
        status_code=303
    )


@router.get("/all", response_model=list[ArticleRead])
def get_articles(db: Session = Depends(get_db)):
    return db.query(Article).order_by(Article.id.desc()).all()


@router.get("/article/{article_id}")
def article_page(
    article_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    article = db.query(Article).filter(Article.id == article_id).first()

    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    author = db.query(User).filter(User.id == article.user_id).first()

    return templates.TemplateResponse(
        request=request,
        name="article_detail.html",
        context={
            "article": article,
            "author": author,
            "user": current_user
        }
    )



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
