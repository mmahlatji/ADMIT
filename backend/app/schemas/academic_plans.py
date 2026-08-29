import uuid

from pydantic import BaseModel

from app.models.academic_plans import AcademicPlanType


class AcademicPlanCreate(BaseModel):
    """Fields the client supplies to create an academic plan."""

    department_code: str
    academic_plan: str
    plan_type: AcademicPlanType


class AcademicPlanUpdate(BaseModel):
    """Partial update for an academic plan, only set fields are applied."""

    department_code: str | None = None
    academic_plan: str | None = None
    plan_type: AcademicPlanType | None = None


class AcademicPlanResponse(AcademicPlanCreate):
    """What an academic plan looks like over the wire."""

    academic_plan_id: uuid.UUID

    model_config = {"from_attributes": True}
