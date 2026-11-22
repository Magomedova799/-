
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import joinedload

from app.database import Base, engine
from app.dependencies import get_db, get_optional_user
from app.models.user import User
from app.models.project import Project
from app.models.article import Article
from app.models.course import Course

import app.models

from app.routers.pages import router as pages_router
from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.categories import router as categories_router
from app.routers.articles import router as articles_router
from app.routers.lessons import router as lessons_router
from app.routers.courses import router as courses_router
from app.routers import assignments
from app.routers import tests
from app.routers import social


app = FastAPI(
    title="DevSpace",
    description="Платформа для начинающих разработчиков",
    version="1.0.0"
)

templates = Jinja2Templates(directory="templates")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

Base.metadata.create_all(bind=engine)


@app.get("/")
async def home(
    request: Request,
    db=Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    courses = db.query(Course).all()

    projects = (
        db.query(Project)
        .options(joinedload(Project.user))
        .order_by(Project.created_at.desc())
        .all()
    )

    articles = db.query(Article).all()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "DevSpace",
            "courses": courses,
            "projects": projects,
            "articles": articles,
            "user": user
        }
    )


@app.get("/create")
def create_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="create.html",
        context={}
    )


app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(categories_router)
app.include_router(articles_router)
app.include_router(lessons_router)
app.include_router(courses_router)
app.include_router(assignments.router)
app.include_router(tests.router)
app.include_router(social.router)

