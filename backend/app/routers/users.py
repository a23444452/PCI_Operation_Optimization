from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_role
from app.models.user import User, UserPermission
from app.schemas.common import ok
from app.schemas.user import (
    UpdateUserPermissions,
    UpdateUserRole,
    UpdateUserStatus,
    UserListItem,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])

VALID_ROLES = {"admin", "editor", "viewer"}
VALID_STATUSES = {"active", "inactive", "pending"}
VALID_PERMISSIONS = {"offload_override", "data_mgmt", "risk_mgmt"}


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    users = db.query(User).order_by(User.id).all()
    items = [
        UserListItem(
            id=u.id,
            username=u.username,
            display_name=u.display_name,
            email=u.email,
            role=u.role,
            status=u.status,
            permissions=[p.feature_key for p in u.permissions],
        )
        for u in users
    ]
    return ok(items)


@router.patch("/{user_id}/role")
def update_user_role(
    user_id: int,
    body: UpdateUserRole,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    if body.role not in VALID_ROLES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid role. Must be one of: {', '.join(sorted(VALID_ROLES))}",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = body.role
    db.commit()
    return ok({"message": "Role updated"})


@router.patch("/{user_id}/status")
def update_user_status(
    user_id: int,
    body: UpdateUserStatus,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.status = body.status
    db.commit()
    return ok({"message": "Status updated"})


@router.put("/{user_id}/permissions")
def set_user_permissions(
    user_id: int,
    body: UpdateUserPermissions,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    invalid = set(body.permissions) - VALID_PERMISSIONS
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid permissions: {', '.join(sorted(invalid))}. "
            f"Must be from: {', '.join(sorted(VALID_PERMISSIONS))}",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.query(UserPermission).filter(UserPermission.user_id == user_id).delete()
    for key in body.permissions:
        db.add(UserPermission(user_id=user_id, feature_key=key))
    db.commit()
    return ok({"message": "Permissions updated"})
