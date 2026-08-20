"""Pydantic schemas for system logs (scalar-only; audit data)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SystemLogCreate(BaseModel):
    entity_name: str = Field(min_length=1)
    entity_id: UUID
    old_data: dict[str, Any]
    new_data: dict[str, Any]
    changed_by: str = Field(min_length=1, max_length=7)
    reason: str = Field(min_length=1)
    import_run_id: UUID | None = None


class SystemLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: UUID
    old_data: dict[str, Any]
    new_data: dict[str, Any]
    changed_by: str
    changed_at: datetime
    reason: str
    import_run_id: UUID | None
