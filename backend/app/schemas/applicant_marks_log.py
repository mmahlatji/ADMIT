"""Pydantic schemas for applicant marks log (scalar-only; audit data)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApplicantMarkLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campus_id: str
    course_code: str
    new_mark: float
    prev_mark: float | None
    updated_at: datetime
    updated_by: str
