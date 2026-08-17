"""Pydantic schemas for applicant marks.

ApplicantMarkCreate -> fields the client supplies.
ApplicantMarkResponse -> scalar fields from the DB row.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApplicantMarkCreate(BaseModel):
    campus_id: str
    course_code: str
    mark: float


class ApplicantMarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mark_id: int
    campus_id: str
    course_code: str
    mark: float
    created_at: datetime
