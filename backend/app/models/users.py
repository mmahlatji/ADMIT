import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .notes import Note
    from .votes import Vote


class RoleEnum(str, Enum):
    """The three roles a user can hold. Null role means not approved yet."""

    admin = "admin"
    convenor = "convenor"
    committee = "committee"


class User(Base):
    __tablename__ = "users"
    # declared explicitly on top of the unique index that unique=True gives
    # employee_id below. The approved_by self-FK needs a real unique
    # constraint to reference at table-creation time, and stating it here
    # keeps the model matching the migration so `alembic check` stays clean.
    __table_args__ = (UniqueConstraint("employee_id", name="users_employee_id_key"),)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    # required: the signup form collects it and Supabase carries it through as
    # user metadata, so every account has one from the moment it is created.
    employee_id: Mapped[str] = mapped_column(
        String(7), unique=True, index=True, nullable=False
    )
    # still optional, unlike employee_id: a bare Supabase JWT carries only
    # sub/email, so these stay unset unless signup sent them as metadata.
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[RoleEnum | None] = mapped_column(
        SQLEnum(RoleEnum, name="roles"), nullable=True
    )  # staff waiting on approval will have null roles
    # set explicitly by whichever service grants/revokes a role, not inferred by the db
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.employee_id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    notes: Mapped[list[Note]] = relationship(back_populates="author")
    votes: Mapped[list[Vote]] = relationship(back_populates="voter")
