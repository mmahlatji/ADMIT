"""Pydantic schemas for academic programs (scalar-only; lookup data)."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AcademicProgramCreate(BaseModel):
    academic_program_code: str = Field(min_length=1)
    academic_program: str | None = None


class AcademicProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    academic_program_id: UUID
    academic_program_code: str
    academic_program: str | None
