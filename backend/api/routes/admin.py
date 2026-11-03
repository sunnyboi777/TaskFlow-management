
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.orm import load_only

from ...core.database import get_db
from ... import models
from ...models.task import Task
from ...schemas.auth import UserOut
from .auth import require_admin


router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
)


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    is_active: bool
    created_at: object


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserRoleUpdate(BaseModel):
    role: Literal["admin", "user"]


class BulkUserStatusUpdate(BaseModel):
    user_ids: list[int]
    is_active: bool


def preserve_user_tasks(db: Session, user_ids: list[int]):
    """Keep tasks in the database when their owner account is deleted."""

    if user_ids:
        db.query(Task).filter(
            Task.user_id.in_(user_ids)
        ).update(
            {Task.user_id: None},
            synchronize_session=False,
        )


@router.get(
    "/users",
    response_model=list[AdminUserOut],
)
def get_all_users(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    return (
        db.query(models.User)
        .options(
            load_only(
                models.User.id,
                models.User.email,
                models.User.role,
                models.User.is_active,
                models.User.created_at,
            )
        )
        .order_by(models.User.id)
        .all()
    )


@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    update: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    user = db.get(models.User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    if user.id == admin.id and not update.is_active:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own admin account.",
        )

    if user.role == "admin" and user.is_active and not update.is_active:
        active_admins = db.query(models.User).filter(
            models.User.role == "admin",
            models.User.is_active.is_(True),
        ).count()

        if active_admins <= 1:
            raise HTTPException(
                status_code=400,
                detail="The last active administrator cannot be deactivated.",
            )

    user.is_active = update.is_active
    db.commit()
    db.refresh(user)

    return {
        "message": "User status updated successfully.",
        "user": UserOut.model_validate(user),
    }


@router.patch("/users/bulk-status")
def update_users_status_bulk(
    update: BulkUserStatusUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    user_ids = list(set(update.user_ids))

    if not user_ids:
        raise HTTPException(
            status_code=400,
            detail="Select at least one account.",
        )

    users = db.query(models.User).filter(
        models.User.id.in_(user_ids)
    ).all()

    if len(users) != len(user_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more selected accounts were not found.",
        )

    if not update.is_active:
        if admin.id in user_ids:
            raise HTTPException(
                status_code=400,
                detail="Your own administrator account cannot be deactivated.",
            )

        active_admins = db.query(models.User).filter(
            models.User.role == "admin",
            models.User.is_active.is_(True),
        ).count()

        selected_active_admins = sum(
            1 for user in users
            if user.role == "admin" and user.is_active
        )

        if active_admins - selected_active_admins < 1:
            raise HTTPException(
                status_code=400,
                detail="At least one active administrator must remain.",
            )

    try:
        updated_count = (
            db.query(models.User)
            .filter(models.User.id.in_(user_ids))
            .update(
                {models.User.is_active: update.is_active},
                synchronize_session=False,
            )
        )
        db.commit()

        return {
            "message": "Selected account statuses updated successfully.",
            "updated_count": updated_count,
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to update selected accounts.",
        )


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    update: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    user = db.get(models.User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    if user.id == admin.id and update.role != "admin":
        raise HTTPException(
            status_code=400,
            detail="You cannot remove your own admin role.",
        )

    if (
        user.role == "admin"
        and update.role == "user"
        and user.is_active
    ):
        active_admins = db.query(models.User).filter(
            models.User.role == "admin",
            models.User.is_active.is_(True),
        ).count()

        if active_admins <= 1:
            raise HTTPException(
                status_code=400,
                detail="The last active administrator cannot be demoted.",
            )

    user.role = update.role
    db.commit()
    db.refresh(user)

    return {
        "message": "User role updated successfully.",
        "user": UserOut.model_validate(user),
    }


@router.delete("/users/inactive")
def delete_all_inactive_users(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """Delete every inactive account in one database transaction."""

    inactive_user_ids = select(models.User.id).where(
        models.User.is_active.is_(False),
        models.User.id != admin.id,
    )

    try:
        db.query(Task).filter(
            Task.user_id.in_(inactive_user_ids)
        ).update(
            {Task.user_id: None},
            synchronize_session=False,
        )

        deleted_count = (
            db.query(models.User)
            .filter(
                models.User.is_active.is_(False),
                models.User.id != admin.id,
            )
            .delete(synchronize_session=False)
        )

        if not deleted_count:
            db.commit()
            return {
                "message": "There are no inactive accounts to delete.",
                "deleted_count": 0,
            }

        db.commit()

        return {
            "message": "All inactive accounts deleted successfully.",
            "deleted_count": deleted_count,
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to delete inactive accounts.",
        )


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """Delete one account directly while preserving its tasks."""

    user = db.get(models.User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    if user.id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own administrator account.",
        )

    if user.role == "admin" and user.is_active:
        active_admins = db.query(models.User).filter(
            models.User.role == "admin",
            models.User.is_active.is_(True),
        ).count()

        if active_admins <= 1:
            raise HTTPException(
                status_code=400,
                detail="The last active administrator cannot be deleted.",
            )

    try:
        preserve_user_tasks(db, [user.id])
        db.delete(user)
        db.commit()

        return {
            "message": "Account deleted successfully.",
            "user_id": user_id,
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to delete this account.",
        )
