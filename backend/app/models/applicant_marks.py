import uuid
from datetime import datetime, timezone
from sqlalchemy import Float, ForeignKey, DateTime, String, PrimaryKeyConstraint, CheckConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.deps import Base
from .applicants import Applicant

class ApplicantMark(Base):
    __tablename__="applicant_marks"
    mark_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"))
    course_code: Mapped[str] = mapped_column(ForeignKey("courses.course_code"), nullable=False, index=True)
    mark: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)

    applicant: Mapped["Applicant"] = relationship(back_populates="applicant_marks")


    __table_args__ = (
        CheckConstraint(
            "mark >= 0 AND mark <= 100",
            name="course_mark_constraint"
        )
    )


#TODO: Review
"""
1.  A table dedicated to tracking which courses belong to a academic plan and program ?
2.  Updates should fill the logging table (use a trigger)
"""