"""Pydantic schemas for votes.

VoteCreate -> fields the client supplies.
VoteResponse -> scalar fields from the DB row.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VoteCreate(BaseModel):
    application_number: str = Field(min_length=1)
    campus_id: str= Field(min_length=1)
    vote: str
    voter_id: str = Field(min_length=1, max_length=7)


class VoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vote_id: int
    application_number: str
    campus_id: str
    vote: str
    voter_id: str
    voted_at: datetime
