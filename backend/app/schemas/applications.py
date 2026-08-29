import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.applications import ApplicationStatus, Choice, DenyReason, Semester


class ApplicationCreate(BaseModel):
    """Fields the client supplies to create an application."""

    application_number: str
    campus_id: str
    academic_program_code: str
    academic_plan1: str
    choice: Choice
    application_status: ApplicationStatus
    application_date: date
    effective_date: date
    semester: Semester | None = None
    last_registration: str | None = None
    previous_application_term: int | None = None
    incorrect_plan: bool = False
    duplicate_application: bool = False
    application_status_reason: DenyReason | None = None
    requires_plan_correction: bool = False


class ApplicationUpdate(BaseModel):
    """Partial update for an application, only set fields are applied."""

    application_number: str | None = None
    campus_id: str | None = None
    academic_program_code: str | None = None
    academic_plan1: str | None = None
    choice: Choice | None = None
    application_status: ApplicationStatus | None = None
    semester: Semester | None = None
    application_date: date | None = None
    effective_date: date | None = None
    last_registration: str | None = None
    previous_application_term: int | None = None
    incorrect_plan: bool | None = None
    duplicate_application: bool | None = None
    application_status_reason: DenyReason | None = None
    requires_plan_correction: bool | None = None


class ApplicationResponse(ApplicationCreate):
    """What an application looks like over the wire."""

    application_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
