import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .applicants import Applicant
from .application_lifecycles import ApplicationLifecycle
from .base import Base
from .votes import Vote

if TYPE_CHECKING:
    from .applicants import Applicant
    from .application_lifecycles import ApplicationLifecycle
    from .votes import Vote
class AcademicCareer(str, Enum):
    HONOURS = "hons"
    MASTERS = "msc"
    DOCTORATE = "phd"

class Choice(str, Enum):
    FIRST = "first"
    SECOND = "second"

class Semester(str, Enum):
    FIRST = "first"
    SECOND = "second"

class Application(Base):
    __tablename__="applications"
    application_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    application_number: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), nullable=False, index=True)
    academic_program_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    academic_plan1: Mapped[str] = mapped_column(String(255), nullable=False)
    academic_plan2: Mapped[str] = mapped_column(String(255), nullable=True) # if you only apply for one program, can even be removed probably because it will exist in another row
    academic_career: Mapped[AcademicCareer] = mapped_column(SQLEnum(AcademicCareer, name="academic_career"), nullable=False, default=AcademicCareer.HONOURS, index=True) # can be changed if ASR also includes undergrad
    application_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    choice: Mapped[Choice] = mapped_column(SQLEnum(Choice, name="choice"), nullable=False, index=True)
    admit_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    semester: Mapped[Semester] = mapped_column(SQLEnum(Semester, name="semester"), nullable=False)
    last_registration: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    application_term: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    previous_application_term: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True) # maybe they never applied at all
    import_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("import_runs.import_run_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    applicant: Mapped["Applicant"] = relationship(back_populates="applications")
    votes: Mapped[list["Vote"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    application_lifecycle: Mapped["ApplicationLifecycle"] = relationship(back_populates="application")

    
#TODO: Review below
"""
1.  Since another application can exist in another row the there would be no need to have an academic plan2 we can can just query applications for an applicant for a 
    specific term and it would be there
2.  Admit_type, semester and academic program unknow and might need enums 
3.  Representation of dates in last registration, application date and previous term application unknown it could be a date or a datetime so could change.
"""