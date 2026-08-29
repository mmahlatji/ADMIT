from app.models.academic_plans import AcademicPlanType
from app.queries.academic_plans import (
    create_academic_plan,
    delete_academic_plan,
    get_academic_plan_by_id,
    get_academic_plans,
    update_academic_plan,
)
from app.queries.departments import create_department


def test_create_and_get_academic_plan(db_session):
    create_department(db_session, "CSC")
    plan = create_academic_plan(db_session, "CSC", "CSC05", AcademicPlanType.INTERNAL)

    fetched = get_academic_plan_by_id(db_session, plan.academic_plan_id)
    assert fetched is not None
    assert fetched.plan_type == AcademicPlanType.INTERNAL


def test_get_academic_plans_returns_all(db_session):
    create_department(db_session, "CSC")
    create_academic_plan(db_session, "CSC", "CSC05", AcademicPlanType.INTERNAL)
    create_academic_plan(db_session, "CSC", "CSC06", AcademicPlanType.EXTERNAL)

    assert len(get_academic_plans(db_session)) == 2


def test_update_academic_plan_only_sets_passed_fields(db_session):
    create_department(db_session, "CSC")
    plan = create_academic_plan(db_session, "CSC", "CSC05", AcademicPlanType.INTERNAL)

    updated = update_academic_plan(db_session, plan, plan_type=AcademicPlanType.EXTERNAL)
    assert updated.academic_plan == "CSC05"
    assert updated.plan_type == AcademicPlanType.EXTERNAL


def test_delete_academic_plan(db_session):
    create_department(db_session, "CSC")
    plan = create_academic_plan(db_session, "CSC", "CSC05", AcademicPlanType.INTERNAL)

    delete_academic_plan(db_session, plan)

    assert get_academic_plan_by_id(db_session, plan.academic_plan_id) is None
