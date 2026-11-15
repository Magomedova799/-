import os
import uuid

from fastapi import (APIRouter, Depends,HTTPException,UploadFile,File, Form)
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead


router = APIRouter(
    prefix="/projects",
    tags=["Проекты"]
)


@router.post("/create", response_model=ProjectRead)
def create_project(
    title: str = Form(...),
    description: str = Form(...),
    technologies: str = Form(...),
    category_id: int | None = Form(None),
    github_url: str | None = Form(None),
    demo_url: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    image_url = None

    if file:
        allowed_types = ["image/jpeg", "image/png", "image/webp"]

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Разрешены только JPG, PNG и WEBP"
            )

        extension = os.path.splitext(file.filename)[1].lower()

        filename = f"{uuid.uuid4()}{extension}"

        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as image:
            image.write(file.file.read())

        image_url = f"/static/uploads/{filename}"

    project = Project(
        title=title,
        description=description,
        technologies=technologies,
        category_id=category_id,
        github_url=github_url,
        demo_url=demo_url,
        image_url=image_url,
        user_id=current_user.id
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


@router.get("/", response_model=list[ProjectRead])
def get_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.id.desc()).all()
    return projects

@router.get("/search/projects", response_model=list[ProjectRead])
def search_projects(
    title: str,
    db: Session = Depends(get_db)
):
    projects = db.query(Project).filter(
        Project.title.ilike(f"%{title}%")
    ).all()

    if projects is None:
        raise HTTPException(
            status_code=404,
            detail="Проект не найден"
        )

    return projects

@router.get("/category/{category_id}", response_model=list[ProjectRead])
def get_projects_by_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    projects = db.query(Project).filter(
        Project.category_id == category_id
    ).order_by(Project.id.desc()).all()

    return projects

@router.put("/{project_id}/editing", response_model=ProjectRead)
def update_project(
    project_id: int,
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Проект не найден"
        )

    project.title = data.title
    project.description = data.description
    project.technologies = data.technologies
    project.category_id = data.category_id
    project.github_url = data.github_url
    project.demo_url = data.demo_url
    project.image_url = data.image_url

    db.commit()
    db.refresh(project)

    return project


@router.delete("/{project_id}/delete")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Проект не найден"
        )

    db.delete(project)
    db.commit()

    return {"message": "Проект успешно удалён"}