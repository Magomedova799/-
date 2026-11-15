from fastapi import APIRouter, Depends,  HTTPException
from sqlalchemy.orm import Session

from sqlalchemy import select
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
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = Project(
        title=data.title,
        description=data.description,
        technologies=data.technologies,
        category_id=data.category_id,
        github_url=data.github_url,
        demo_url=data.demo_url,
        image_url=data.image_url,
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

@router.get("/search", response_model=list[ProjectRead])
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