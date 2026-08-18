"""Pydantic schemas for courses (scalar-only; lookup data)."""

from pydantic import BaseModel, ConfigDict


class CourseCreate(BaseModel):
    academic_program_code: str
    course_code: str
    course_name: str | None = None


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: int
    academic_program_code: str
    course_code: str
    course_name: str | None
