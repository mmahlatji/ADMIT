import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .applicants import Applicant

class ResultCode(str, Enum):
    PA = "PA"
    DE = "DE"
    OSS = "OSS"
    AB = "AB"
    F = "F"
    # a supplementary exam was granted, e.g. a cell of "47S". Same NN<letter>
    # shape as the fail codes, see the result code table in the dataset README
    S = "S"
    NONE = "NONE"
    
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
    mark: Mapped[int] = mapped_column(Integer, nullable=False)
    result_code: Mapped[ResultCode] = mapped_column(SQLEnum(ResultCode, name="result_code"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    applicant: Mapped["Applicant"] = relationship(back_populates="applicant_marks", foreign_keys=[campus_id])


