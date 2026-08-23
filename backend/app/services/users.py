import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.users import RoleEnum, User
from app.queries import users as user_queries

ALLOWED_EMAIL_DOMAINS = {"uct.ac.za", "myuct.ac.za"}


class DomainNotAllowedError(Exception):
    """Raised when a login's email isn't on a UCT domain."""


def is_allowed_domain(email: str) -> bool:
    """Check whether an email's domain is on the UCT allowlist."""
    domain = email.rsplit("@", 1)[-1].lower()
    return domain in ALLOWED_EMAIL_DOMAINS


def get_or_create_user(db: Session, claims: dict) -> User:
    """Resolve a verified JWT's claims to a user row, creating one on first login."""
    email = claims["email"]
    if not is_allowed_domain(email):
        raise DomainNotAllowedError(email)

    user_id = uuid.UUID(claims["sub"])
    existing = user_queries.get_user_by_id(db, user_id)
    if existing is not None:
        return existing

    # Name is optional: only present if the frontend sent it as signup metadata.
    metadata = claims.get("user_metadata") or {}
    first_name = metadata.get("first_name")
    last_name = metadata.get("last_name")

    return user_queries.create_user(db, user_id, email, first_name, last_name)


def assign_role(db: Session, actor: User, target: User, role: RoleEnum | None) -> User:
    """Grant or revoke a user's role. actor is whoever's making the change."""
    # Checked again here even though the router already enforces this, so this
    # stays safe if it's ever called from somewhere other than that one endpoint.
    if actor.role != RoleEnum.convenor:
        raise PermissionError("Only a convenor can assign or revoke roles")

    # approved_at/approved_by record the last grant, not revocation, so that
    # info survives a later revoke instead of being overwritten by it.
    approved_by = actor.employee_id if role is not None else None
    approved_at = datetime.now(UTC) if role is not None else None
    return user_queries.update_user_role(db, target, role, approved_by, approved_at)
