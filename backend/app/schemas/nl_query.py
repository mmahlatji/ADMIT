import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

QueryResult = int | list[dict[str, Any]]


class QueryRequest(BaseModel):
    """The only thing the client sends for a new query: a natural-language question."""

    prompt: str


class QueryAskResponse(BaseModel):
    """A newly saved query's id, title, and first page of results."""

    query_id: uuid.UUID
    rows: QueryResult | None = None
    title: str | None = None


class SavedQueryMeta(BaseModel):
    """Metadata for one saved query, for the history list."""

    model_config = ConfigDict(from_attributes=True)

    query_id: uuid.UUID
    prompt: str
    title: str | None = None
    created_at: datetime
