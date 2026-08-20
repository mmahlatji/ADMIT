"""Pydantic schemas for matching reviews.

MatchingReviewCreate -> fields the client supplies.
MatchingReviewResponse -> scalar fields from the DB row.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MatchingReviewCreate(BaseModel):
    staging_row_id: UUID
    candidate_keys: dict[str, Any] | None = None
    match_signals: dict[str, Any] | None = None
    status: str = Field(min_length=1)
    resolved_by: str = Field(min_length=1, max_length=7)
    resolution: str | None = None
    reason: str | None = None


class MatchingReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: UUID
    staging_row_id: UUID
    candidate_keys: dict[str, Any] | None
    match_signals: dict[str, Any] | None
    status: str
    resolved_by: str
    resolution: str | None
    reason: str | None
    resolved_at: datetime | None
