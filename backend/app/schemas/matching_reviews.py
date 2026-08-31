import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.matching_reviews import MatchResolution, MatchStatus


class MatchingReviewCreate(BaseModel):
    """Fields the client supplies to create a matching review."""

    staging_row_id: uuid.UUID
    status: MatchStatus
    candidate_keys: dict[str, Any] | None = None
    match_signals: dict[str, Any] | None = None
    resolved_by: str | None = None
    resolution: MatchResolution | None = None
    reason: str | None = None


class MatchingReviewUpdate(BaseModel):
    """Partial update for a matching review, only set fields are applied."""

    staging_row_id: uuid.UUID | None = None
    status: MatchStatus | None = None
    candidate_keys: dict[str, Any] | None = None
    match_signals: dict[str, Any] | None = None
    resolved_by: str | None = None
    resolution: MatchResolution | None = None
    reason: str | None = None


class MatchingReviewResponse(MatchingReviewCreate):
    """What a matching review looks like over the wire."""

    match_id: uuid.UUID
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}


class ResolveReviewRequest(BaseModel):
    """Request body for resolving a matching review."""

    resolution: MatchResolution
    reason: str | None = None
