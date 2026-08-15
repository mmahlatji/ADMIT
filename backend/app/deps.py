"""Shared FastAPI dependencies: DB session, current user, role checks."""

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase


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
    raise NotImplementedError


def require_role(*allowed_roles: str):
    def _check(user=Depends(get_current_user)):
        if getattr(user, "role", None) not in allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted")
        return user

    return _check

class Base(DeclarativeBase):
    pass
