from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.deps import Base


class ApplicantMarkLog(Base):
    __tablename__="applicant_marks_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), nullable=False)
    course_code: Mapped[str] = mapped_column(ForeignKey("courses.course_code"), nullable=False)
    new_mark: Mapped[float] = mapped_column(Float, nullable=False)
    prev_mark: Mapped[float] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=False)