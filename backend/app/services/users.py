import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.system_logs import ChangeSource
from app.models.users import RoleEnum, User
from app.queries import system_logs as system_log_queries
from app.queries import users as user_queries

ALLOWED_EMAIL_DOMAINS = {"uct.ac.za", "myuct.ac.za"}


class DomainNotAllowedError(Exception):
    """Raised when a login's email isn't on a UCT domain."""


class MissingEmployeeIdError(Exception):
    """Raised when a first login carries no employee_id in its signup metadata."""


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

    # employee_id is not optional. The signup form collects it and Supabase
    # carries it through as metadata, so a token without one means the account
    # was made outside our signup flow. Fail readably instead of letting it hit
    # the NOT NULL constraint as a raw IntegrityError.
    employee_id = metadata.get("employee_id")
    if not employee_id:
        raise MissingEmployeeIdError(email)

    return user_queries.create_user(
        db, user_id, email, employee_id, first_name, last_name
    )


def assign_role(db: Session, actor: User, target: User, role: RoleEnum | None) -> User:
    """Grant or revoke a user's role. actor is whoever's making the change."""
    # Checked again here even though the router already enforces this, so this
    # stays safe if it's ever called from somewhere other than that one endpoint.
    if actor.role != RoleEnum.convenor:
        raise PermissionError("Only a convenor can assign or revoke roles")
    # convenor cannot revoke their own role (lock themselves out basically)
    if actor.user_id == target.user_id:
        raise PermissionError("Cannot change your own role")
    # approved_at/approved_by record the last grant, not revocation, so that
    # info survives a later revoke instead of being overwritten by it.
    approved_by = actor.employee_id if role is not None else None
    approved_at = datetime.now(UTC) if role is not None else None
    old_role = target.role
    user = user_queries.update_user_role(db, target, role, approved_by, approved_at)
    system_log_queries.create_system_log(
        db,
        entity_name="users",
        entity_id=target.user_id,
        changed_by=actor.employee_id or str(actor.user_id),  # this may be a problem
        reason=ChangeSource.MANUAL_EDIT,
        old_data={"role": old_role},
        new_data={"role": role},
    )
    return user


# ther router called the queries directly which violated the layered architecture
# so i added this
def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return user_queries.get_user_by_id(db, user_id)
