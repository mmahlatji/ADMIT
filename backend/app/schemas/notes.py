"""Pydantic schemas for notes.

NoteCreate -> fields the client supplies.
NoteResponse -> scalar fields from the DB row.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):
    campus_id: str
    author_id: str
    content: str


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note_id: int
    campus_id: str
    author_id: str
    content: str
    created_at: datetime
