import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Boolean, Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .applicant_marks import ApplicantMark
    from .applications import Application
    from .motivations import Motivation
    from .notes import Note


class Applicant(Base):
    __tablename__="applicants"
    applicant_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    campus_id: Mapped[str] = mapped_column(String(9), unique=True, index=True, nullable=False)
    employee_id: Mapped[str] = mapped_column(String(7), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False,  unique=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=False)
    sex: Mapped[str] = mapped_column(String(255), nullable=False) # I dont know if I should use an enum{Male, Female, Other} or what ?
    cell_phone: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    home_phone: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    population_group: Mapped[str] = mapped_column(String(15), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    citizenship_residency: Mapped[str] = mapped_column(String(255), nullable=False)
    non_sa_citizenship: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True) # index if we filter based on citizenship
    applied_for_academic_program: Mapped[bool] = mapped_column(Boolean, nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=True, unique=True) # TODO: change this when you implement the document table/ remove and have documents refer to applicants
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    applications: Mapped[list["Application"]] = relationship(back_populates="applicant", cascade="all, delete-orphan") # so now we can access applications with applicant.applications
    applicant_marks: Mapped[list["ApplicantMark"]] = relationship(back_populates="applicant", cascade="all, delete-orphan")
    notes: Mapped[list["Note"]] = relationship(back_populates="applicant", cascade="all, delete-orphan")
    motivation: Mapped["Motivation"] = relationship(back_populates="applicant", cascade="all, delete-orphan", uselist=False)






