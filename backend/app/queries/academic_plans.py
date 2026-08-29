import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic_plans import AcademicPlan, AcademicPlanType


def get_academic_plan_by_id(db: Session, academic_plan_id: uuid.UUID) -> AcademicPlan | None:
    """Look up an academic plan by its id. Returns None if it doesn't exist yet."""
    return db.execute(
        select(AcademicPlan).where(AcademicPlan.academic_plan_id == academic_plan_id)
    ).scalar_one_or_none()


def get_academic_plans(db: Session, skip: int = 0, limit: int = 100) -> list[AcademicPlan]:
    """List academic plans, paginated."""
    return list(db.execute(select(AcademicPlan).offset(skip).order_by(AcademicPlan.academic_plan.asc()).limit(limit)).scalars())


def create_academic_plan(
    db: Session, department_code: str, academic_plan: str, plan_type: AcademicPlanType
) -> AcademicPlan:
    """Insert a new academic plan row."""
    plan = AcademicPlan(
        academic_plan_id=uuid.uuid4(),
        department_code=department_code,
        academic_plan=academic_plan,
        plan_type=plan_type,
    )
    db.add(plan)
    db.flush()
    db.refresh(plan)
    return plan


def update_academic_plan(
    db: Session,
    plan: AcademicPlan,
    department_code: str | None = None,
    academic_plan: str | None = None,
    plan_type: AcademicPlanType | None = None,
) -> AcademicPlan:
    """Partially update an academic plan, only sets fields explicitly passed."""
    fields = {
        "department_code": department_code,
        "academic_plan": academic_plan,
        "plan_type": plan_type,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(plan, field, value)
    db.flush()
    db.refresh(plan)
    return plan


def delete_academic_plan(db: Session, plan: AcademicPlan) -> None:
    """Delete an academic plan row."""
    db.delete(plan)
    db.flush()
