import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.import_runs import ImportStatus, SourceType


class ImportRunCreate(BaseModel):
    """Fields the client supplies to start a new import run."""

    source_type: SourceType
    uploaded_by: str
    file_name: str
    status: ImportStatus
    rows_total: int
    rows_loaded: int = 0
    rows_rejected: int = 0
    rows_auto_matched: int = 0
    rows_auto_new: int = 0
    rows_flagged: int = 0


class ImportRunUpdate(BaseModel):
    """Partial update for an import run, only set fields are applied."""

    source_type: SourceType | None = None
    uploaded_by: str | None = None
    file_name: str | None = None
    status: ImportStatus | None = None
    rows_total: int | None = None
    rows_loaded: int | None = None
    rows_rejected: int | None = None
    rows_auto_matched: int | None = None
    rows_auto_new: int | None = None
    rows_flagged: int | None = None


class ImportRunResponse(ImportRunCreate):
    """What an import run looks like over the wire."""

    import_run_id: uuid.UUID
    uploaded_at: datetime

    model_config = {"from_attributes": True}
