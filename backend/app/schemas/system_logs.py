import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.system_logs import ChangeSource


class SystemLogCreate(BaseModel):
    """Fields the client supplies to create a system log entry."""

    entity_name: str
    entity_id: uuid.UUID
    changed_by: str
    reason: ChangeSource
    # nullable=True isn't set on these in the model, but they're JSON columns:
    # a Python None serializes to the JSON literal "null", not a SQL NULL, so
    # it satisfies the NOT NULL constraint - these are effectively optional.
    old_data: dict[str, Any] | None = None
    new_data: dict[str, Any] | None = None
    import_run_id: uuid.UUID | None = None


class SystemLogUpdate(BaseModel):
    """Partial update for a system log entry, only set fields are applied."""

    entity_name: str | None = None
    entity_id: uuid.UUID | None = None
    changed_by: str | None = None
    old_data: dict[str, Any] | None = None
    new_data: dict[str, Any] | None = None
    reason: ChangeSource | None = None
    import_run_id: uuid.UUID | None = None


class SystemLogResponse(SystemLogCreate):
    """What a system log entry looks like over the wire."""

    log_id: uuid.UUID
    changed_at: datetime

    model_config = {"from_attributes": True}
