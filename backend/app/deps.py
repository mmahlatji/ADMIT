"""Shared FastAPI dependencies: DB session, current user, role checks.

Every router handler that touches data depends on get_db here — no
router or service should construct its own session.
"""

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user():
    """Decode and verify the Supabase-issued JWT from the Authorization header.

    This only establishes identity, not authorization — new signups start
    with role = null (see require_role below).
    """
    raise NotImplementedError


def require_role(*allowed_roles: str):
    """Dependency factory: 403s unless the current user's role is allowed.

    role = null (an unapproved signup) never satisfies any role check —
    the convenor must assign a role via POST /users/{id}/role first.
    """

    def _check(user=Depends(get_current_user)):
        if getattr(user, "role", None) not in allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted")
        return user

    return _check
