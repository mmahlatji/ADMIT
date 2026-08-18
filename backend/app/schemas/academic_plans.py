"""Pydantic schemas for academic plans (scalar-only; lookup data)."""

from pydantic import BaseModel, ConfigDict


class AcademicPlanCreate(BaseModel):
    academic_plan: str
    academic_program_code: str


class AcademicPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    academic_plan_id: int
    academic_plan: str
    academic_program_code: str
