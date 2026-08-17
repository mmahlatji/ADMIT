"""Pydantic schemas for applicants.

ApplicantCreate  -> fields the client supplies (created_at is server-generated).
ApplicantResponse -> scalar fields from the DB row.
ApplicantResponseWithDetails -> response plus nested related entities.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .applicant_marks import ApplicantMarkResponse
from .applications import ApplicationResponse
from .motivations import MotivationResponse
from .notes import NoteResponse


class ApplicantCreate(BaseModel):
    campus_id: str = Field(max_length=9)
    employee_id: str = Field(max_length=7)
    first_name: str = Field(max_length=255)
    last_name: str = Field(max_length=255)
    sex: str = Field(max_length=255)
    cell_phone: str = Field(max_length=255)
    home_phone: str = Field(max_length=255)
    email: EmailStr = Field(max_length=255)
    population_group: str = Field(max_length=15)
    birth_date: date
    citizenship_residency: str = Field(max_length=255)
    non_sa_citizenship: bool
    applied_for_academic_program: bool
    document_id: UUID | None = None


class ApplicantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    campus_id: str
    employee_id: str
    first_name: str
    last_name: str
    sex: str
    cell_phone: str
    home_phone: str
    email: EmailStr
    population_group: str
    birth_date: date
    citizenship_residency: str
    non_sa_citizenship: bool
    applied_for_academic_program: bool
    document_id: UUID | None
    created_at: datetime


class ApplicantResponseWithDetails(ApplicantResponse):
    applications: list[ApplicationResponse] = Field(default_factory=list)
    applicant_marks: list[ApplicantMarkResponse] = Field(default_factory=list)
    notes: list[NoteResponse] = Field(default_factory=list)
    motivation: MotivationResponse | None = None
