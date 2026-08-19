from typing import TYPE_CHECKING
from datetime import UTC, datetime
import uuid
from sqlalchemy import DateTime, ForeignKey, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
if TYPE_CHECKING:
    from .notes import Note
    from .votes import Vote

class User(Base):
    __tablename__="users"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(7), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(255), nullable=True) # staff waiting on approval will have null roles
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(UTC))
    approved_by: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    notes: Mapped[list["Note"]] = relationship(back_populates="author")
    votes: Mapped[list["Vote"]] = relationship(back_populates="voter")

