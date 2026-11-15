from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.categories import router as categories_router

app = FastAPI(
    title="DevSpace API",
    description="Платформа для начинающих разработчиков",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(categories_router)