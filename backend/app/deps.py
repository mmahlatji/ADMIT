"""Shared FastAPI dependencies: DB session, current user, role checks."""

from collections.abc import Generator
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models.user import RoleEnum, User
from app.services.users import DomainNotAllowedError, get_or_create_user

_bearer_scheme = HTTPBearer()


@lru_cache
def get_engine():
    """Build the DB engine once and reuse it. Lazy so a blank DATABASE_URL doesn't crash imports."""
    return create_engine(get_settings().database_url)


@lru_cache
def get_jwks_client() -> PyJWKClient:
    """Client that fetches and caches Supabase's public keys for verifying JWTs."""
    url = f"{get_settings().supabase_url}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(url)


def get_db() -> Generator[Session, None, None]:
    """Per-request DB session, closed once the request is done."""
    session_local = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    db = session_local()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Verify the request's bearer token and resolve it to a user row."""
    token = credentials.credentials
    try:
        signing_key = get_jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key=signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc

    try:
        return get_or_create_user(db, claims)
    except DomainNotAllowedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Email domain not permitted") from exc
    except (KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token claims") from exc


def require_role(*allowed_roles: RoleEnum):
    """Returns a dependency that 403s unless the current user's role is one of allowed_roles."""

    def _check(user=Depends(get_current_user)):
        if getattr(user, "role", None) not in allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted")
        return user

    return _check
