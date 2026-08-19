"""Pydantic schemas for notes.

NoteCreate -> fields the client supplies.
NoteResponse -> scalar fields from the DB row.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    campus_id: str = Field(min_length=1)
    author_id: str = Field(min_length=1, max_digits=7)
    content: str = Field(min_length=1)


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note_id: int
    campus_id: str
    author_id: str
    content: str
    created_at: datetime
