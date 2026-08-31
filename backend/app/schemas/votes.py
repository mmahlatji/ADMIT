import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.votes import VoteDecision


class VoteCreate(BaseModel):
    """Fields the client supplies to create a vote."""

    application_number: str
    campus_id: str
    vote: VoteDecision
    voter_id: str


class VoteCreateRequest(BaseModel):
    """Fields the client supplies to cast a vote. The voter is the logged-in user."""

    application_number: str
    vote: VoteDecision


class VoteUpdate(BaseModel):
    """Partial update for a vote, only set fields are applied."""

    application_number: str | None = None
    campus_id: str | None = None
    vote: VoteDecision | None = None
    voter_id: str | None = None


class VoteResponse(VoteCreate):
    """What a vote looks like over the wire."""

    vote_id: uuid.UUID
    voted_at: datetime

    model_config = {"from_attributes": True}
