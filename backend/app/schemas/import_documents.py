import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentCreate(BaseModel):
    """Fields the client supplies to create an import-run document (e.g. the raw uploaded file)."""

    import_run_id: uuid.UUID
    storage_key: uuid.UUID
    original_file_name: str
    content_type: str
    sha256_hash: str


class DocumentUpdate(BaseModel):
    """Partial update for an import-run document, only set fields are applied."""

    import_run_id: uuid.UUID | None = None
    storage_key: uuid.UUID | None = None
    original_file_name: str | None = None
    content_type: str | None = None
    sha256_hash: str | None = None


class DocumentResponse(DocumentCreate):
    """What an import-run document looks like over the wire."""

    document_id: uuid.UUID
    uploaded_at: datetime

    model_config = {"from_attributes": True}
