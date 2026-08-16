import uuid
from datetime import datetime, timezone
from sqlalchemy import UUID, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.deps import Base
from .applicants import Applicant


class Note(Base):
    __tablename__="notes"
    note_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), nullable=False, index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    applicant: Mapped["Applicant"] = relationship(back_populates="notes")