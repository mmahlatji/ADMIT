import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db, require_role
from app.models.users import RoleEnum, User
from app.schemas.user import RoleAssignment, UserOut
from app.services.users import assign_role, get_user_by_id

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_current_user(user: User = Depends(get_current_user)) -> User:
    """Return the logged-in user, even if their role is still null."""
    return user


@router.post("/{user_id}/role", response_model=UserOut)
def set_user_role(
    user_id: uuid.UUID,
    body: RoleAssignment,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.convenor)),
) -> User:
    """Grant or revoke a user's role. convenor only."""
    target = get_user_by_id(db, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return assign_role(db, actor, target, body.role)
