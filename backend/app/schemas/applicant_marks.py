"""Pydantic schemas for applicant marks.

ApplicantMarkCreate -> fields the client supplies.
ApplicantMarkResponse -> scalar fields from the DB row.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApplicantMarkCreate(BaseModel):
    campus_id: str = Field(min_length=1, max_length=9)
    course_code: str = Field(min_length=1, max_length=8)
    mark: float = Field(ge=0, le=100)


class ApplicantMarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mark_id: int
    campus_id: str
    course_code: str
    mark: float
    created_at: datetime
