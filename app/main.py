from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from app.database import Base, engine
from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.categories import router as categories_router
from app.models import Subscription, Like, Comment
from app.models.poll import Poll
from app.routers.polls import router as polls_router
from app.routers.articles import router as articles_router
from app.routers.lessons import router as lessons_router
from app.routers.courses import router as courses_router
from app.routers import assignments, tests, social
from app.routers.search import router as search_router

BASE_DIR = Path(__file__).resolve().parents[1]
app = FastAPI(
    title="DevSpace API",
    description="Платформа для начинающих разработчиков",
    version="1.1.0",
)
Base.metadata.create_all(bind=engine)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def render_page(page: str, item_id: int | None = None):
    template = BASE_DIR / "templates" / "app.html"
    html = template.read_text(encoding="utf-8")
    return HTMLResponse(
        html.replace("__PAGE__", page).replace("__ID__", str(item_id or ""))
    )


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(BASE_DIR / "templates" / "index.html")


@app.get("/login", include_in_schema=False)
def login_page():
    return render_page("login")


@app.get("/register", include_in_schema=False)
def register_page():
    return render_page("register")


@app.get("/profile", include_in_schema=False)
def profile_page():
    return render_page("profile")


@app.get("/create", include_in_schema=False)
def create_page():
    return render_page("create")


@app.get("/search", include_in_schema=False)
def search_page():
    return render_page("search")


@app.get("/course/{item_id}", include_in_schema=False)
def course_page(item_id: int):
    return render_page("course", item_id)


@app.get("/article/{item_id}", include_in_schema=False)
def article_page(item_id: int):
    return render_page("article", item_id)


@app.get("/project/{item_id}", include_in_schema=False)
def project_page(item_id: int):
    return render_page("project", item_id)


@app.get("/poll/{item_id}", include_in_schema=False)
def poll_page(item_id: int):
    return render_page("poll", item_id)


@app.get("/lesson/{item_id}", include_in_schema=False)
def lesson_page(item_id: int):
    return render_page("lesson", item_id)


@app.get("/test/{item_id}", include_in_schema=False)
def test_page(item_id: int):
    return render_page("test", item_id)


app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(categories_router)
app.include_router(polls_router)
app.include_router(articles_router)
app.include_router(lessons_router)
app.include_router(courses_router)
app.include_router(assignments.router)
app.include_router(tests.router)
app.include_router(social.router)
app.include_router(search_router)
