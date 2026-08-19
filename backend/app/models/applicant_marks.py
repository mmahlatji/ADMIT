from datetime import UTC, datetime
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .applicants import Applicant


class ApplicantMark(Base):
    __tablename__="applicant_marks"
    mark_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), nullable=False)
    course_code: Mapped[str] = mapped_column(ForeignKey("courses.course_code"), nullable=False, index=True)
    mark: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC), nullable=False, index=True)

    applicant: Mapped["Applicant"] = relationship(back_populates="applicant_marks", foreign_keys=[campus_id])


    __table_args__ = (
        CheckConstraint(
            "mark >= 0 AND mark <= 100",
            name="course_mark_constraint"
        ),
    )


#TODO: Review
"""
1.  A table dedicated to tracking which courses belong to a academic plan and program ?
2.  Updates should fill the logging table (use a trigger)
"""