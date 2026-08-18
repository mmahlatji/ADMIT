"""Pydantic schemas for system logs (scalar-only; audit data)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SystemLogCreate(BaseModel):
    entity_name: str
    entity_id: str
    old_data: dict[str, Any]
    new_data: dict[str, Any]
    changed_by: str
    reason: str
    import_run_id: str | None = None


class SystemLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: int
    entity_name: str
    entity_id: str
    old_data: dict[str, Any]
    new_data: dict[str, Any]
    changed_by: str
    changed_at: datetime
    reason: str
    import_run_id: str | None
