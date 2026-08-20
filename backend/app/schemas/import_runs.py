"""Pydantic schemas for import runs.

ImportRunCreate -> fields the client supplies.
ImportRunResponse -> scalar fields from the DB row.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ImportRunCreate(BaseModel):
    source_type: str = Field(min_length=1)
    uploaded_by: str = Field(min_length=1, max_length=7)
    file_name: str = Field(min_length=1, max_length=255)
    status: str = Field(min_length=1)
    rows_total: int
    rows_loaded: int
    rows_rejected: int
    rows_auto_matched: int
    rows_auto_new: int
    rows_flagged: int


class ImportRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    import_run_id: UUID
    source_type: str
    uploaded_by: str
    uploaded_at: datetime
    file_name: str
    status: str
    rows_total: int
    rows_loaded: int
    rows_rejected: int
    rows_auto_matched: int
    rows_auto_new: int
    rows_flagged: int
