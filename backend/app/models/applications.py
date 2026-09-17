import uuid
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .applicants import Applicant
from .base import Base
from .votes import Vote

if TYPE_CHECKING:
    from .applicants import Applicant
    from .external_applicants_data import ExternalApplicantData
    from .votes import Vote

class Choice(str, Enum):
    FIRST = "FRST"
    SECOND = "SCND"

class Semester(str, Enum):
    FIRST = "1st Semester"
    SECOND = "2nd Semester"
    UNSPECIFIED = "unspecified"

class ApplicationStatus(str, Enum):
    APPLIED = "Applied"
    REVIEWED = "Reviewed"    
    CONDITIONAL_OFFER = "Conditional Offer"
    ACCEPTED = "Accepted"
    READY_TO_REGISTER = "Ready to Register"
    DENIED = "Denied"
    CANCELLED = "Cancelled"


class DenyReason(str, Enum):
    NOT_COMPETITIVE = "Not competitive"
    REQUIREMENTS_NOT_MET = "Requirements not met"
    DUPLICATE_APPLICATION = "Duplicate application"
    INCORRECT_PROGRAM = "Incorrect program"


class Application(Base):
    __tablename__="applications"
    application_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    application_number: Mapped[str] = mapped_column(String(8), unique=True, index=True, nullable=False)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), nullable=False, index=True)
    academic_program_code: Mapped[str] = mapped_column(String(5), nullable=False)
    academic_plan1: Mapped[str] = mapped_column(String(10), nullable=False)
    choice: Mapped[Choice] = mapped_column(SQLEnum(Choice, name="choice", values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False, index=True)
    semester: Mapped[Semester] = mapped_column(SQLEnum(Semester, name="semester", values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=True)
    application_date: Mapped[date] = mapped_column(Date, index=True)
    effective_date: Mapped[date] = mapped_column(Date, index=True)
    application_status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus, name="application_status", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
                    nullable=False, index=True
                )
    last_registration: Mapped[str] = mapped_column(String(100), nullable=True)
    previous_application_term: Mapped[int] = mapped_column(Integer, nullable=True) # maybe they never applied at all in the past

    incorrect_plan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    duplicate_application: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    application_status_reason: Mapped[DenyReason | None] = mapped_column(
        SQLEnum(DenyReason, name="deny_reson", values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=True)
    requires_plan_correction: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False) # if an application is incorrect and a decision has been made but that is the only application for that applicant
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    applicant: Mapped[Applicant] = relationship(back_populates="applications")
    votes: Mapped[list[Vote]] = relationship(back_populates="application", cascade="all, delete-orphan")
    external_applicant_data: Mapped[ExternalApplicantData] = relationship(back_populates="application", cascade="all, delete-orphan")

    