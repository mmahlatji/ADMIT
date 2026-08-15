from datetime import date, datetime
from sqlalchemy import Float, ForeignKey, DateTime, String, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.deps import Base

class ApplicantMark(Base):
    __tablename__="applicant_marks"
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"))
    course_code: Mapped[str] = mapped_column(String(8))
    mark: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


    __table_args__ = (
        PrimaryKeyConstraint(
            "campus_id",
            "course_code",
        ),
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