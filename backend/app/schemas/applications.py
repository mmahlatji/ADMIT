"""Pydantic schemas for applications.

ApplicationCreate -> fields the client supplies.
ApplicationResponse -> scalar fields from the DB row.
ApplicationResponseWithDetails -> response plus nested related entities.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .application_lifecycles import ApplicationLifecycleResponse
from .votes import VoteResponse


class ApplicationCreate(BaseModel):
    application_number: str
    campus_id: str
    academic_program_code: str
    academic_plan1: str
    academic_plan2: str | None
    academic_career: str
    application_date: datetime
    choice: str
    admit_type: str | None
    semester: str
    last_registration: datetime | None
    application_term: datetime
    previous_application_term: datetime | None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_number: str
    campus_id: str
    academic_program_code: str
    academic_plan1: str
    academic_plan2: str | None
    academic_career: str
    application_date: datetime
    choice: str
    admit_type: str | None
    semester: str
    last_registration: datetime | None
    application_term: datetime
    previous_application_term: datetime | None


class ApplicationResponseWithDetails(ApplicationResponse):
    votes: list[VoteResponse] = Field(default_factory=list)
    application_lifecycle: ApplicationLifecycleResponse | None = None
