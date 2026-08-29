import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.applicants import CitizenshipResidency, SexEnum, TitleEnum


class ApplicantCreate(BaseModel):
    """Fields the client supplies to create an applicant."""

    campus_id: str
    employee_id: str
    title: TitleEnum
    first_name: str
    last_name: str
    citizenship_residency: CitizenshipResidency
    sex: SexEnum | None = None
    cell_phone: str | None = None
    home_phone: str | None = None
    email: str | None = None
    population_group: str | None = None
    birth_date: date | None = None
    non_sa_citizenship: str | None = None


class ApplicantUpdate(BaseModel):
    """Partial update for an applicant, only set fields are applied."""

    campus_id: str | None = None
    employee_id: str | None = None
    title: TitleEnum | None = None
    first_name: str | None = None
    last_name: str | None = None
    citizenship_residency: CitizenshipResidency | None = None
    sex: SexEnum | None = None
    cell_phone: str | None = None
    home_phone: str | None = None
    email: str | None = None
    population_group: str | None = None
    birth_date: date | None = None
    non_sa_citizenship: str | None = None


class ApplicantResponse(ApplicantCreate):
    """What an applicant looks like over the wire."""

    applicant_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
