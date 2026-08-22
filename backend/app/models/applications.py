import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .applicants import Applicant
from .base import Base
from .votes import Vote

if TYPE_CHECKING:
    from .applicants import Applicant
    from .votes import Vote


class Choice(str, Enum):
    FIRST = "first"
    SECOND = "second"

class Semester(str, Enum):
    FIRST = "first"
    SECOND = "second"

class AdmitType(str, Enum):
    NEW = "new"
    NPG = "npg"
    UCT = "uct"
    CON = "con"
    REM = "rem"
    RAD = "rad"

# these are how we distinguish if it is a new or continuing student
NEW_TYPES = {
    AdmitType.NEW,
    AdmitType.NPG,
}

UCT_TYPES = {
    AdmitType.UCT,
    AdmitType.CON,
    AdmitType.REM,
    AdmitType.RAD,
}

class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    REVIEWED = "reviewed"
    CONDITIONALLY_ACCEPTED = "conditionally accepted"
    ACCEPTED = "accepted"
    READY_TO_REGISTER = "ready to register"
    FIRM_OFFER = "firm offer"
    DENY_R = "deny: requirements not met"
    DENY_N = "deny: not competitive"
    DENY_RD = "deny: requirements not met (duplicate application)"


class Application(Base):
    __tablename__="applications"
    application_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    application_number: Mapped[str] = mapped_column(String(8), unique=True, index=True, nullable=False)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), nullable=False, index=True)
    academic_program_code: Mapped[str] = mapped_column(String(10), nullable=False)
    academic_plan1: Mapped[str] = mapped_column(String(255), nullable=False)
    academic_plan2: Mapped[str] = mapped_column(String(255), nullable=True) # if you only apply for one program, can even be removed probably because it will exist in another row
    choice: Mapped[Choice] = mapped_column(SQLEnum(Choice, name="choice"), nullable=False, index=True)
    admit_type: Mapped[AdmitType] = mapped_column(SQLEnum(AdmitType, name="admit_types"), nullable=True)
    semester: Mapped[Semester] = mapped_column(SQLEnum(Semester, name="semester"), nullable=False)
    application_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    effective_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    application_status: Mapped[ApplicationStatus] = mapped_column(SQLEnum(ApplicationStatus, name="application_status"), nullable=False, index=True)
    last_registration: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    application_term: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    previous_application_term: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True) # maybe they never applied at all
    import_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("import_runs.import_run_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    applicant: Mapped["Applicant"] = relationship(back_populates="applications")
    votes: Mapped[list["Vote"]] = relationship(back_populates="application", cascade="all, delete-orphan")

    
#TODO: Review below
"""
1.  Since another application can exist in another row the there would be no need to have an academic plan2 we can can just query applications for an applicant for a 
    specific term and it would be there
2.  Admit_type, semester and academic program unknow and might need enums 
3.  Representation of dates in last registration, application date and previous term application unknown it could be a date or a datetime so could change.
"""