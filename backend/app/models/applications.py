from app.deps import Base
from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Enum as SQLEnum, DateTime
from datetime import datetime 

class AcademicCareer(Enum):
    HONOURS = "hons"
    MASTERS = "msc"
    DOCTORATE = "phd"

class Choice(Enum):
    FIRST = "first"
    SECOND = "second"

class Semester(Enum):
    FIRST = "first"
    SECOND = "second"

class Application(Base):
    __tablename__="applications"
    application_number: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), nullable=False, index=True)
    academic_program_code: Mapped[str] = mapped_column(ForeignKey("academic_program.academic_program_code"), nullable=False, index=True)
    academic_plan1: Mapped[str] = mapped_column(String(255), nullable=False)
    academic_plan2: Mapped[str] = mapped_column(String(255), nullable=True) # if you only apply for one program, can even be removed probably because it will exist in another row
    academic_career: Mapped[AcademicCareer] = mapped_column(SQLEnum(AcademicCareer, name="academic_career"), nullable=False, default=AcademicCareer.HONOURS, index=True) # can be changed if ASR also includes undergrad
    application_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    choice: Mapped[Choice] = mapped_column(SQLEnum(Choice, name="choice"), nullable=False, index=True)
    admit_type: Mapped[Choice] = mapped_column(String(255), nullable=True)
    semester: Mapped[Semester] = mapped_column(SQLEnum(Semester, name="semester"), nullable=False)
    last_registration: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    previous_application_term: Mapped[datetime] = mapped_column(DateTime, nullable=True) # maybe they never applied at all

#TODO: Review below
"""
1.  Since another application can exist in another row the there would be no need to have an academic plan2 we can can just query applications for an applicant for a 
    specific term and it would be there
2.  Admit_type, semester and academic program unknow and might need enums 
3.  Representation of dates in last registration, application date and previous term application unknown it could be a date or a datetime so could change.
4.  Remember to check timezones if necessarry
"""