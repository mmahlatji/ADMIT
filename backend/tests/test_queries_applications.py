from datetime import date

from app.models.applications import ApplicationStatus, Choice, DenyReason
from app.queries.applications import (
    create_application,
    delete_application,
    get_application_by_id,
    get_application_by_number,
    get_applications,
    get_applications_by_intake_year,
    get_applications_by_status_and_year,
    intake_year_bounds,
    update_application,
)
from tests.test_queries_applicants import _create as create_applicant


def _create(db_session, application_number="00000001"):
    create_applicant(db_session)
    return create_application(
        db_session,
        application_number=application_number,
        campus_id="xxxyyy001",
        academic_program_code="CSC",
        academic_plan1="CSC05",
        choice=Choice.FIRST,
        application_status=ApplicationStatus.APPLIED,
        application_date=date(2022, 10, 1),
        effective_date=date(2022, 10, 1),
    )


def test_create_and_get_application(db_session):
    application = _create(db_session)

    fetched = get_application_by_id(db_session, application.application_id)
    assert fetched is not None
    assert fetched.application_status == ApplicationStatus.APPLIED
    assert fetched.incorrect_plan is False


def test_get_applications_returns_all(db_session):
    create_applicant(db_session)
    create_application(
        db_session,
        application_number="00000001",
        campus_id="xxxyyy001",
        academic_program_code="CSC",
        academic_plan1="CSC05",
        choice=Choice.FIRST,
        application_status=ApplicationStatus.APPLIED,
        application_date=date(2022, 10, 1),
        effective_date=date(2022, 10, 1),
    )
    create_application(
        db_session,
        application_number="00000002",
        campus_id="xxxyyy001",
        academic_program_code="CSC",
        academic_plan1="CSC06",
        choice=Choice.SECOND,
        application_status=ApplicationStatus.APPLIED,
        application_date=date(2022, 10, 1),
        effective_date=date(2022, 10, 1),
    )

    assert len(get_applications(db_session)) == 2


def test_update_application_only_sets_passed_fields(db_session):
    application = _create(db_session)

    updated = update_application(
        db_session,
        application,
        application_status=ApplicationStatus.DENIED,
        application_status_reason=DenyReason.NOT_COMPETITIVE,
    )
    assert updated.application_number == "00000001"
    assert updated.application_status == ApplicationStatus.DENIED
    assert updated.application_status_reason == DenyReason.NOT_COMPETITIVE


def test_delete_application(db_session):
    application = _create(db_session)

    delete_application(db_session, application)

    assert get_application_by_id(db_session, application.application_id) is None


def test_get_application_by_number(db_session):
    _create(db_session)

    found = get_application_by_number(db_session, "00000001")
    assert found is not None
    assert found.application_number == "00000001"

    assert get_application_by_number(db_session, "doesnotexist") is None


def test_paging_applications_is_stable_across_ties(db_session):
    # Every row shares a campus_id, which was the whole sort key: without a
    # unique tiebreaker the database is free to order these differently per
    # query, so a row could appear on two pages or on none.
    create_applicant(db_session)
    for i in range(6):
        create_application(
            db_session,
            application_number=f"APP{i:03d}",
            campus_id="xxxyyy001",
            academic_program_code="CSC",
            academic_plan1="CSC05",
            choice=Choice.FIRST,
            application_status=ApplicationStatus.APPLIED,
            application_date=date(2022, 10, 1),
            effective_date=date(2022, 10, 1),
        )

    seen = []
    for skip in (0, 2, 4):
        seen.extend(a.application_id for a in get_applications(db_session, skip=skip, limit=2))

    assert len(seen) == 6
    assert len(set(seen)) == 6

def test_intake_year_bounds_span_the_whole_preceding_year():
    start, end = intake_year_bounds(2023)

    assert start == date(2022, 1, 1)
    assert end == date(2023, 1, 1)


def test_a_late_application_still_belongs_to_the_intake(db_session):
    """The rule engine read a hardcoded April-September window, so an
    application dated October was never evaluated and sat at Applied no
    matter how often the rules were run."""
    # _create dates the application 2022-10-01, which that window excluded.
    _create(db_session)

    found = get_applications_by_status_and_year(
        db_session, [ApplicationStatus.APPLIED], 2023
    )

    assert [a.application_number for a in found] == ["00000001"]


def test_an_application_outside_the_intake_is_not_returned(db_session):
    _create(db_session)

    assert get_applications_by_status_and_year(
        db_session, [ApplicationStatus.APPLIED], 2024
    ) == []
    assert get_applications_by_intake_year(db_session, 2024) == []


def test_the_export_and_the_rule_engine_agree_on_the_intake(db_session):
    _create(db_session)

    exported = get_applications_by_intake_year(db_session, 2023)
    evaluated = get_applications_by_status_and_year(
        db_session, [ApplicationStatus.APPLIED], 2023
    )

    assert [a.application_id for a in exported] == [
        a.application_id for a in evaluated
    ]
