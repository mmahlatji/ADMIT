from datetime import UTC, datetime
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import DateTime, ForeignKey, Integer, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .applicants import Applicant
    from .users import User

class Note(Base):
    __tablename__="notes"
    note_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), nullable=False, index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    applicant: Mapped["Applicant"] = relationship(back_populates="notes", foreign_keys=[campus_id])
    author: Mapped["User"] = relationship(back_populates="notes")