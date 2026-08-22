import uuid
from datetime import datetime, UTC
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey, String, func, Enum as SQLEnum
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
    __tablename__="users"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(7), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[RoleEnum] = mapped_column(SQLEnum(RoleEnum, name="roles"), nullable=True) # staff waiting on approval will have null roles
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(UTC))
    approved_by: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    notes: Mapped[list["Note"]] = relationship(back_populates="author")
    votes: Mapped[list["Vote"]] = relationship(back_populates="voter")

