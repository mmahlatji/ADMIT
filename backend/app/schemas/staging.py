"""Pydantic schemas for staging rows.

StagingCreate -> fields the client supplies.
StagingResponse -> scalar fields from the DB row.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StagingCreate(BaseModel):
    import_run_id: UUID
    entity: str = Field(min_length=1)
    raw_data: dict[str, Any]
    normalized_data: dict[str, Any]
    validation_status: str = Field(min_length=1)
    rejection_reason: str | None = None
    matched_application_id: str | None = None
    matched_campus_id: str | None = None


class StagingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    staging_id: UUID
    import_run_id: UUID
    raw_data: dict[str, Any]
    normalized_data: dict[str, Any]
    validation_status: str
    rejection_reason: str | None
    matched_application_id: str | None
    matched_campus_id: str | None
