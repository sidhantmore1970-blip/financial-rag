from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core import models
from core.schemas import RegisterBody, LoginBody, TokenOut
from core.auth import make_hash, check_pass, make_token

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(body: RegisterBody, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    email_exists = db.query(models.User).filter(models.User.email == body.email).first()
    if email_exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        username=body.username,
        email=body.email,
        password_hash=make_hash(body.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "message": "Registered successfully"}


@router.post("/login", response_model=TokenOut)
def login_user(body: LoginBody, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == body.username).first()
    if not user or not check_pass(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong username or password")

    token = make_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
