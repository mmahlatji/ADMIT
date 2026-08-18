"""Pydantic schemas for academic programs (scalar-only; lookup data)."""

from pydantic import BaseModel, ConfigDict


class AcademicProgramCreate(BaseModel):
    academic_program_code: str
    academic_program: str | None = None


class AcademicProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    academic_program_id: int
    academic_program_code: str
    academic_program: str | None
