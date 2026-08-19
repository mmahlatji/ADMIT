"""Pydantic schemas for academic plans (scalar-only; lookup data)."""

from pydantic import BaseModel, ConfigDict, Field


class AcademicPlanCreate(BaseModel):
    academic_plan: str = Field(min_length=1)
    academic_program_code: str = Field(min_length=1)


class AcademicPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    academic_plan_id: int
    academic_plan: str
    academic_program_code: str
