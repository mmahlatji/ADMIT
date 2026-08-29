import uuid

from pydantic import BaseModel


class ExternalApplicantDataCreate(BaseModel):
    """Fields the client supplies to create an external applicant's screening data."""

    application_number: str
    missing_documents: str | None = None
    prev_university_and_degree: str | None = None
    correct_previous_degree: bool | None = None
    degree_completed: bool | None = None
    has_min_viable_marks: bool | None = None
    comment: str | None = None


class ExternalApplicantDataUpdate(BaseModel):
    """Partial update for external applicant data, only set fields are applied."""

    application_number: str | None = None
    missing_documents: str | None = None
    prev_university_and_degree: str | None = None
    correct_previous_degree: bool | None = None
    degree_completed: bool | None = None
    has_min_viable_marks: bool | None = None
    comment: str | None = None


class ExternalApplicantDataResponse(ExternalApplicantDataCreate):
    """What external applicant data looks like over the wire."""

    ea_id: uuid.UUID

    model_config = {"from_attributes": True}
