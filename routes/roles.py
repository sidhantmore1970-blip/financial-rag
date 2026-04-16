from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core import models
from core.schemas import RoleCreate, RoleOut, AssignRoleBody
from core.auth import get_logged_in_user, check_permission

router = APIRouter()


@router.post("/roles/create", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(
    body: RoleCreate,
    db: Session = Depends(get_db),
    curr_user: models.User = Depends(check_permission("full_access"))
):
    already_exists = db.query(models.Role).filter(models.Role.role_name == body.role_name).first()
    if already_exists:
        raise HTTPException(status_code=400, detail="Role already exists")

    new_role = models.Role(role_name=body.role_name, permissions=body.permissions)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


@router.post("/users/assign-role", status_code=status.HTTP_200_OK)
def assign_role_to_user(
    body: AssignRoleBody,
    db: Session = Depends(get_db),
    curr_user: models.User = Depends(check_permission("full_access"))
):
    user = db.query(models.User).filter(models.User.id == body.user_id).first()
    role = db.query(models.Role).filter(models.Role.id == body.role_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role not in user.roles:
        user.roles.append(role)
        db.commit()

    return {"message": f"Role '{role.role_name}' assigned to '{user.username}'"}


@router.get("/users/{user_id}/roles", response_model=list[RoleOut])
def get_roles_of_user(
    user_id: int,
    db: Session = Depends(get_db),
    curr_user: models.User = Depends(get_logged_in_user)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.roles


@router.get("/users/{user_id}/permissions")
def get_permissions_of_user(
    user_id: int,
    db: Session = Depends(get_db),
    curr_user: models.User = Depends(get_logged_in_user)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    perm_set = set()
    for r in user.roles:
        for p in r.permissions.split(","):
            cleaned = p.strip()
            if cleaned:
                perm_set.add(cleaned)

    return {"user_id": user_id, "permissions": sorted(perm_set)}
