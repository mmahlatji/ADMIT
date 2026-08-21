import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey, Text, func
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    applicant: Mapped["Applicant"] = relationship(back_populates="notes", foreign_keys=[campus_id])
    author: Mapped["User"] = relationship(back_populates="notes")