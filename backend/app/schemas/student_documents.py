import uuid
from datetime import datetime

from pydantic import BaseModel


class StudentDocumentCreate(BaseModel):
    """Fields the client supplies to create a student document (e.g. a transcript upload)."""

    applicant_id: uuid.UUID
    storage_key: str
    original_file_name: str
    content_type: str
    sha256_hash: str


class StudentDocumentUpdate(BaseModel):
    """Partial update for a student document, only set fields are applied."""

    applicant_id: uuid.UUID | None = None
    storage_key: str | None = None
    original_file_name: str | None = None
    content_type: str | None = None
    sha256_hash: str | None = None


class StudentDocumentResponse(StudentDocumentCreate):
    """What a student document looks like over the wire."""

    document_id: uuid.UUID
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class StudentDocumentDownloadResponse(BaseModel):
    """Carries the short lived download link."""

    original_file_name: str
    signed_url: str
    content_type: str
