import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.article import Article
from app.models.user import User
from app.schemas.article import ArticleCreate, ArticleRead


router = APIRouter(prefix="/articles", tags=["Статьи"])
BASE_DIR = Path(__file__).resolve().parents[2]


async def save_article_image(image: UploadFile | None) -> str | None:
    if image is None or not image.filename:
        return None

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    extension = allowed_types.get(image.content_type or "")
    if extension is None:
        raise HTTPException(400, "Разрешены только JPG, PNG и WEBP")

    content = await image.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "Изображение не должно превышать 5 МБ")

    upload_dir = BASE_DIR / "static" / "uploads" / "articles"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}{extension}"
    (upload_dir / filename).write_bytes(content)
    return f"/static/uploads/articles/{filename}"


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


@router.post("/create-with-image", response_model=ArticleRead)
async def create_article_with_image(
    title: str = Form(...),
    content: str = Form(...),
    category_id: int | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(title.strip()) < 3:
        raise HTTPException(422, "Заголовок должен содержать минимум 3 символа")
    if len(content.strip()) < 10:
        raise HTTPException(422, "Текст статьи должен содержать минимум 10 символов")

    image_url = await save_article_image(image)
    article = Article(
        user_id=current_user.id,
        title=title.strip(),
        content=content.strip(),
        category_id=category_id,
        image_url=image_url,
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
    article = db.query(Article).filter(Article.id == article_id).first()
    if article is None:
        raise HTTPException(404, "Статья не найдена")
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
        raise HTTPException(404, "Статья не найдена")

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
        raise HTTPException(404, "Статья не найдена")

    db.delete(article)
    db.commit()
    return {"message": "Статья успешно удалена"}
