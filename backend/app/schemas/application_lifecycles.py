"""Pydantic schemas for application lifecycles.

ApplicationLifecycleCreate -> fields the client supplies.
ApplicationLifecycleResponse -> scalar fields from the DB row.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApplicationLifecycleCreate(BaseModel):
    program_action: str
    program_reason: str
    program_status: str
    action_processed_by: str


class ApplicationLifecycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_number: str
    program_action: str
    program_reason: str
    program_status: str
    action_processed_by: str
    action_processed_date: datetime
