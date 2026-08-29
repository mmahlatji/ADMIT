import uuid
from datetime import datetime

from pydantic import BaseModel


class ApplicantMarkCreate(BaseModel):
    """Fields the client supplies to create an applicant mark."""

    campus_id: str
    course_code: str
    # plain string on purpose: real mark cells hold result codes (PA, DE, AB,
    # 44F, ...) mixed with plain integers, not just numbers.
    mark: str


class ApplicantMarkUpdate(BaseModel):
    """Partial update for an applicant mark, only set fields are applied."""

    campus_id: str | None = None
    course_code: str | None = None
    mark: str | None = None


class ApplicantMarkResponse(ApplicantMarkCreate):
    """What an applicant mark looks like over the wire."""

    mark_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
