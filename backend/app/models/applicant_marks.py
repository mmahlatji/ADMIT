import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, CheckConstraint, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .applicants import Applicant


class ApplicantMark(Base):
    __tablename__="applicant_marks"
    mark_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), nullable=False)
    course_code: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    mark: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    applicant: Mapped["Applicant"] = relationship(back_populates="applicant_marks", foreign_keys=[campus_id])


    __table_args__ = (
        CheckConstraint(
            "mark >= 0 AND mark <= 100",
            name="course_mark_constraint"
        ),
    )
