import uuid
from datetime import datetime

from pydantic import BaseModel


class NoteCreate(BaseModel):
    """Fields the client supplies to create a note."""

    campus_id: str
    author_id: str
    content: str


class NoteUpdate(BaseModel):
    """Partial update for a note, only set fields are applied."""

    campus_id: str | None = None
    author_id: str | None = None
    content: str | None = None


class NoteResponse(NoteCreate):
    """What a note looks like over the wire."""

    note_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
