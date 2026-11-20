from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, UserRead, Token , UserUpdate, PasswordUpdate
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Авторизация"])


@router.post("/register", response_model=UserRead)
def register(data: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(
    (User.email == data.email) |
    (User.username == data.username)
).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с такой почтой или именем уже существует")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Неверная почта или пароль"
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserRead)
def update_profile(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_user = db.query(User).filter(
        (User.email == data.email) | (User.username == data.username),
        User.id != current_user.id
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Такая почта или имя уже используются"
        )

    current_user.username = data.username
    current_user.email = data.email
    current_user.bio = data.bio
    current_user.avatar_url = data.avatar_url

    db.commit()
    db.refresh(current_user)

    return current_user

@router.put("/change-password")
def change_password(
    data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Старый пароль указан неправильно"
        )

    current_user.password_hash = hash_password(data.new_password)

    db.commit()

    return {"message": "Пароль успешно изменён"}