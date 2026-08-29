import uuid

from pydantic import BaseModel


class MotivationCreate(BaseModel):
    """Fields the client supplies to create a motivation."""

    campus_id: str
    last_name: str
    first_name: str
    motivation: str | None = None


class MotivationUpdate(BaseModel):
    """Partial update for a motivation, only set fields are applied."""

    campus_id: str | None = None
    last_name: str | None = None
    first_name: str | None = None
    motivation: str | None = None


class MotivationResponse(MotivationCreate):
    """What a motivation looks like over the wire."""

    motivation_id: uuid.UUID

    model_config = {"from_attributes": True}
