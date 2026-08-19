"""Pydantic schemas for application lifecycles.

ApplicationLifecycleCreate -> fields the client supplies.
ApplicationLifecycleResponse -> scalar fields from the DB row.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApplicationLifecycleCreate(BaseModel):
    application_number: str = Field(min_length=1)
    program_action: str = Field(min_length=1)
    program_reason: str = Field(min_length=1)
    program_status: str = Field(min_length=1)
    action_processed_by: str = Field(min_length=1, max_length=9)


class ApplicationLifecycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_lifecycle_id: UUID
    application_number: str
    program_action: str
    program_reason: str
    program_status: str
    action_processed_by: str
    action_processed_date: datetime
