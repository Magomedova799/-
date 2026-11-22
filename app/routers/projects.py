import os
import uuid

from fastapi import (APIRouter, Depends,HTTPException,UploadFile,File, Form)
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead
from fastapi.responses import RedirectResponse
from fastapi import Request
from fastapi.templating import Jinja2Templates
from app.dependencies import get_optional_user
from app.models.like import Like
from app.models.comment import Comment
from app.models.category import Category


router = APIRouter(
    prefix="/projects",
    tags=["Проекты"]
)
templates = Jinja2Templates(directory="templates")

@router.get("/create-page")
def project_create_page(
    request: Request,
    db: Session = Depends(get_db)
):
    categories = db.query(Category).all()

    return templates.TemplateResponse(
        request=request,
        name="project_create.html",
        context={"categories": categories}
    )

@router.post("/create")
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

    if file and file.filename:
        allowed_types = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp"
        }

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Разрешены только JPG, PNG и WEBP"
            )

        extension = allowed_types[file.content_type]
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
        github_url=github_url or None,
        demo_url=demo_url or None,
        image_url=image_url,
        user_id=current_user.id
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return RedirectResponse(
        url="/",
        status_code=303
    )



@router.get("/", response_model=list[ProjectRead])
def get_projects(db: Session = Depends(get_db)):
    projects = (
        db.query(Project)
        .order_by(Project.id.desc())
        .all()
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

@router.get("/{project_id}/edit")
def project_edit_page(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if project is None:
        raise HTTPException(404, "Проект не найден")

    return templates.TemplateResponse(
        request=request,
        name="project_edit.html",
        context={
            "project": project
        }
    )


@router.post("/{project_id}/edit")
def update_project_form(
    project_id: int,
    title: str = Form(...),
    description: str = Form(...),
    technologies: str = Form(...),
    category_id: int | None = Form(None),
    github_url: str | None = Form(None),
    demo_url: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if project is None:
        raise HTTPException(404, "Проект не найден")

    project.title = title
    project.description = description
    project.technologies = technologies
    project.category_id = category_id
    project.github_url = github_url or None
    project.demo_url = demo_url or None

    db.commit()

    return RedirectResponse(
        url=f"/projects/project/{project_id}",
        status_code=303
    )


@router.post("/{project_id}/delete")
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

    return RedirectResponse(
        url="/",
        status_code=303
    )


@router.get("/project/{project_id}")
def project_page(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user)
):
    project = db.query(Project).filter(
        Project.id == project_id
    ).first()

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Проект не найден"
        )

    author = db.query(User).filter(
        User.id == project.user_id
    ).first()

    likes_count = db.query(Like).filter(
        Like.project_id == project_id
    ).count()

    is_liked = False

    if current_user:
        is_liked = db.query(Like).filter(
            Like.project_id == project_id,
            Like.user_id == current_user.id
        ).first() is not None

    comments = (
        db.query(Comment, User.username)
        .join(User, Comment.user_id == User.id)
        .filter(Comment.project_id == project_id)
        .order_by(Comment.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="project_detail.html",
        context={
            "project": project,
            "author": author,
            "current_user": current_user,
            "likes_count": likes_count,
            "is_liked": is_liked,
            "comments": comments
        }
    )


@router.post("/project/{project_id}/like")
def toggle_project_like(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id
    ).first()

    if project is None:
        raise HTTPException(404, "Проект не найден")

    like = db.query(Like).filter(
        Like.project_id == project_id,
        Like.user_id == current_user.id
    ).first()

    if like:
        db.delete(like)
    else:
        db.add(Like(
            user_id=current_user.id,
            project_id=project_id
        ))

    db.commit()

    return RedirectResponse(
        url=f"/projects/project/{project_id}",
        status_code=303
    )


@router.post("/project/{project_id}/comment")
def add_project_comment(
    project_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id
    ).first()

    if project is None:
        raise HTTPException(404, "Проект не найден")

    content = content.strip()

    if not content or len(content) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Комментарий должен содержать от 1 до 2000 символов"
        )

    comment = Comment(
        user_id=current_user.id,
        project_id=project_id,
        content=content
    )

    db.add(comment)
    db.commit()

    return RedirectResponse(
        url=f"/projects/project/{project_id}",
        status_code=303
    )