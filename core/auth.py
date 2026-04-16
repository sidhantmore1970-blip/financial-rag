import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.database import get_db
from core import models


MY_SECRET = os.getenv("SECRET_KEY", "mysecretkey123")
ALGO = "HS256"
EXPIRE_MINS = 480

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def make_hash(raw_pass):
    return pwd_ctx.hash(raw_pass)


def check_pass(raw_pass, hashed):
    return pwd_ctx.verify(raw_pass, hashed)


def make_token(payload: dict):
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINS)
    return jwt.encode(data, MY_SECRET, algorithm=ALGO)


def read_token(token: str):
    try:
        return jwt.decode(token, MY_SECRET, algorithms=[ALGO])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_logged_in_user(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    data = read_token(token)
    uid = data.get("sub")
    if uid is None:
        raise HTTPException(status_code=401, detail="Bad token")
    user = db.query(models.User).filter(models.User.id == int(uid)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def check_permission(perm_name: str):
    def inner(user: models.User = Depends(get_logged_in_user)):
        all_perms = set()
        for r in user.roles:
            for p in r.permissions.split(","):
                all_perms.add(p.strip())
        if "full_access" in all_perms or perm_name in all_perms:
            return user
        raise HTTPException(status_code=403, detail=f"Missing permission: {perm_name}")
    return inner
