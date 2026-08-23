import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users import RoleEnum, User


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    """Look up a user by their id. Returns None if they don't exist yet."""
    return db.execute(select(User).where(User.user_id == user_id)).scalar_one_or_none()


def create_user(
    db: Session,
    user_id: uuid.UUID,
    email: str,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    """Insert a new user row with role=null."""
    user = User(user_id=user_id, email=email, first_name=first_name, last_name=last_name, role=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_role(
    db: Session,
    user: User,
    role: RoleEnum | None,
    approved_by: str | None = None,
    approved_at: datetime | None = None,
) -> User:
    """Set a user's role, and optionally who/when approved it."""
    user.role = role
    if approved_by is not None:
        user.approved_by = approved_by
    if approved_at is not None:
        user.approved_at = approved_at
    db.commit()
    db.refresh(user)
    return user
