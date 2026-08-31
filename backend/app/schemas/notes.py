import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    """Fields the client supplies to create a note."""

    campus_id: str = Field(min_length=1, max_length=9)
    author_id: str = Field(min_length=1)
    content: str = Field(min_length=1)


class NoteUpdate(BaseModel):
    """Partial update for a note, only set fields are applied."""

    campus_id: str | None = Field(min_length=1, max_length=9)
    author_id: str | None = Field(min_length=1, max_length=7)
    content: str | None = None


class NoteResponse(NoteCreate):
    """What a note looks like over the wire."""

    note_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
