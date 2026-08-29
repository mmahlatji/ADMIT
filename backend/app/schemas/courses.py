import uuid

from pydantic import BaseModel


class CourseCreate(BaseModel):
    """Fields the client supplies to create a course."""

    department_code: str
    course_code: str
    course_name: str | None = None


class CourseUpdate(BaseModel):
    """Partial update for a course, only set fields are applied."""

    department_code: str | None = None
    course_code: str | None = None
    course_name: str | None = None


class CourseResponse(CourseCreate):
    """What a course looks like over the wire."""

    course_id: uuid.UUID

    model_config = {"from_attributes": True}
