import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .applicants import Applicant


class ApplicantMark(Base):
    __tablename__="applicant_marks"
    # one mark row per (campus_id, course_code): without this, re-importing an
    # updated mark for a course a student already has on file would insert a
    # duplicate row instead of updating the existing one in place
    __table_args__ = (
        UniqueConstraint("campus_id", "course_code", name="uq_applicant_marks_campus_id_course_code"),
    )

    mark_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), nullable=False)
    course_code: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    mark: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    applicant: Mapped["Applicant"] = relationship(back_populates="applicant_marks", foreign_keys=[campus_id])


