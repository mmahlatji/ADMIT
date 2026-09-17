import uuid
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Date, DateTime, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .applicant_marks import ApplicantMark
    from .applications import Application
    from .motivations import Motivation
    from .notes import Note

class SexEnum(str, Enum):
    MALE = "M"
    FEMALE = "F"

class TitleEnum(str, Enum):
    MR = "Mr"
    MS = "Ms"
    MISS = "Miss"
    UNSPECIFIED = "Unspecified"
    
class CitizenshipResidency(str, Enum):
    SA_CITIZEN = "SA Citizen"
    INTERNATIONAL = "International"
    PERMANENT_RESIDENT = "Permanent Resident"



class Applicant(Base):
    __tablename__="applicants"
    applicant_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    campus_id: Mapped[str] = mapped_column(String(9), unique=True, index=True, nullable=False)
    employee_id: Mapped[str] = mapped_column(String(7), unique=True, nullable=False, index=True) # employee ids are generated alongside campus ids
    title: Mapped[TitleEnum] = mapped_column(
            SQLEnum(TitleEnum, name="title_enum", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
            nullable=False
        )
    first_name: Mapped[str] = mapped_column(String(255), nullable=False,  unique=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=False)
    sex: Mapped[SexEnum] = mapped_column(
            SQLEnum(SexEnum, name="sex_enum", values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=True
        ) 
    cell_phone: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    home_phone: Mapped[str] = mapped_column(String(255), nullable=True, unique=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    population_group: Mapped[str] = mapped_column(String(50), nullable=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=True)
    citizenship_residency: Mapped[CitizenshipResidency] = mapped_column(
            SQLEnum(CitizenshipResidency, name="citizenship_residency", values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False, index=True
        ) # could possibly be an enum
    non_sa_citizenship: Mapped[str] = mapped_column(String(3), nullable=True) 
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    applications: Mapped[list[Application]] = relationship(back_populates="applicant", cascade="all, delete-orphan") # so now we can access applications with applicant.applications
    applicant_marks: Mapped[list[ApplicantMark]] = relationship(back_populates="applicant", cascade="all, delete-orphan")
    notes: Mapped[list[Note]] = relationship(back_populates="applicant", cascade="all, delete-orphan")
    motivation: Mapped[Motivation] = relationship(back_populates="applicant", cascade="all, delete-orphan", uselist=False)






