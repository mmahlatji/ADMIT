import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.applicant_marks import ResultCode


class ApplicantMarkCreate(BaseModel):
    """Fields the client supplies to create an applicant mark."""

    campus_id: str
    course_code: str
    mark: int
    result_code: ResultCode


class ApplicantMarkUpdate(BaseModel):
    """Partial update for an applicant mark, only set fields are applied."""

    campus_id: str | None = None
    course_code: str | None = None
    mark: int | None = None
    result_code: ResultCode | None = None


class ApplicantMarkResponse(ApplicantMarkCreate):
    """What an applicant mark looks like over the wire."""

    mark_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
