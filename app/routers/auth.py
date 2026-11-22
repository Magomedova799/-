
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.user import User
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)

router = APIRouter(tags=["Авторизация"])
templates = Jinja2Templates(directory="templates")


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": request.query_params.get("error")}
    )


@router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse("/login?error=1", status_code=303)

    token = create_access_token(user.id)

    response = RedirectResponse("/profile", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )

    return response


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"error": request.query_params.get("error")}
    )


@router.post("/register")
def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()

    if existing_user:
        return RedirectResponse("/register?error=1", status_code=303)

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    response = RedirectResponse("/profile", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )

    return response


@router.post("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("access_token", path="/")
    return response
