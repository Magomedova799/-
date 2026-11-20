from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

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
from app.routers import assignments
from app.routers import tests
from app.routers import social
from fastapi.responses import FileResponse

app = FastAPI(
    title="DevSpace API",
    description="Платформа для начинающих разработчиков",
    version="1.0.0"
)

@app.get("/", include_in_schema=False)
def home():
    return FileResponse("templates/index.html")

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(categories_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(polls_router)
app.include_router(articles_router)
app.include_router(lessons_router)
app.include_router(courses_router)
app.include_router(assignments.router)
app.include_router(tests.router)
app.include_router(social.router)