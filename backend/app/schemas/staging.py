import uuid
from typing import Any

from pydantic import BaseModel

from app.models.staging import ValidationStatus


class StagingCreate(BaseModel):
    """Fields the client supplies to create a staging row."""

    import_run_id: uuid.UUID
    entity: str
    raw_data: dict[str, Any]
    normalized_data: dict[str, Any]
    validation_status: ValidationStatus
    rejection_reason: str | None = None
    matched_application_id: str | None = None
    matched_campus_id: str | None = None


class StagingUpdate(BaseModel):
    """Partial update for a staging row, only set fields are applied."""

    import_run_id: uuid.UUID | None = None
    entity: str | None = None
    raw_data: dict[str, Any] | None = None
    normalized_data: dict[str, Any] | None = None
    validation_status: ValidationStatus | None = None
    rejection_reason: str | None = None
    matched_application_id: str | None = None
    matched_campus_id: str | None = None


class StagingResponse(StagingCreate):
    """What a staging row looks like over the wire."""

    staging_id: uuid.UUID

    model_config = {"from_attributes": True}
