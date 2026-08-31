from sqlalchemy.orm import Session

from app.models.academic_plans import AcademicPlanType
from app.models.applications import Application
from app.services.academic_plans import get_academic_plans_by_department_code


def get_action_reason(row: dict) -> tuple[str, str] | None:
    """
        Return None when the row carries no (program_action, program_reason)
        entry, otherwise the uppercased  pair. This lets
        the caller tell "missing" from "present but unrecognized".
    """
    action = (row.get("program_action") or "").strip()
    reason = (row.get("program_reason") or "").strip()
    if not action and not reason:
        return None
    return action.upper(), reason.upper()




def determine_duplicate(applications: list) -> Application | None:
    """Return which of two applications is the duplicate, if any.

    Only decides for an unambiguous pair. With three or more there is no single
    obvious duplicate to pick, so this returns None and leaves it to a human -
    the caller flags that case for review.
    """
    if len(applications) != 2:
        return None
    first, second = applications
    if first.academic_plan1[5:8] != second.academic_plan1[5:8]:
        return None
    if first.incorrect_plan:
        return first
    if second.incorrect_plan:
        return second
    return None


def resolve_plans(db: Session, plan_code: str) -> tuple[str | None, str | None] | None:
    """
        Return (internal, external) plan codes for a plan's department, or None
        if the department is unknown.
    """
    department = plan_code[5:8]

    # This runs once per imported row and asks the same question every time, so
    # memoize on Session.info, which is scoped to this session and cleared with
    # it. Only successful lookups are cached: a department that is missing now
    # may be seeded later in the same session, and caching the miss would hide
    # it. Academic plans are reference data and do not change mid-import.
    cache = db.info.setdefault("_academic_plans_by_department", {})
    if department in cache:
        return cache[department]

    plans = get_academic_plans_by_department_code(db, department)
    if not plans:
        return None
    internal = next(
        (plan.academic_plan for plan in plans if plan.plan_type == AcademicPlanType.INTERNAL), None
    )
    external = next(
        (plan.academic_plan for plan in plans if plan.plan_type == AcademicPlanType.EXTERNAL), None
    )
    cache[department] = (internal, external)
    return internal, external





def compute_incorrect_and_requires_plan_change_flags(
    academic_plan1: str,
    last_registration: str | None,
    internal_plan: str | None,
    external_plan: str | None,
) -> tuple[bool, bool]:
    """Determine whether an application is on the wrong plan.

    UCT students (with a last registration) belong on the internal plan;
    non-UCT students belong on the external plan. A department with no
    external plan cannot produce an incorrect application.
    """
    if external_plan is None:
        return False, False

    last_registration = (last_registration or "").strip()
    is_uct_student = last_registration != ""

    if (is_uct_student and academic_plan1 == external_plan) or (
        not is_uct_student and academic_plan1 == internal_plan
    ):
        return True, True
    return False, False