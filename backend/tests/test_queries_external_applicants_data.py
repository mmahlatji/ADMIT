from datetime import date

from app.models.applications import ApplicationStatus, Choice
from app.queries.applications import create_application
from app.queries.external_applicants_data import (
    create_external_applicant_data,
    delete_external_applicant_data,
    get_external_applicant_data_by_id,
    get_external_applicants_data,
    update_external_applicant_data,
)
from tests.test_queries_applications import _create as create_test_application


def _create(db_session, application_number="00000001"):
    create_test_application(db_session, application_number)
    return create_external_applicant_data(
        db_session, application_number, prev_university_and_degree="Wits, BSc"
    )


def test_create_and_get_external_applicant_data(db_session):
    data = _create(db_session)

    fetched = get_external_applicant_data_by_id(db_session, data.ea_id)
    assert fetched is not None
    assert fetched.prev_university_and_degree == "Wits, BSc"


def test_get_external_applicants_data_returns_all(db_session):
    create_test_application(db_session, "00000001")
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
    create_external_applicant_data(db_session, "00000001")
    create_external_applicant_data(db_session, "00000002")

    assert len(get_external_applicants_data(db_session)) == 2


def test_update_external_applicant_data_only_sets_passed_fields(db_session):
    data = _create(db_session)

    updated = update_external_applicant_data(db_session, data, degree_completed=True)
    assert updated.prev_university_and_degree == "Wits, BSc"
    assert updated.degree_completed is True


def test_delete_external_applicant_data(db_session):
    data = _create(db_session)

    delete_external_applicant_data(db_session, data)

    assert get_external_applicant_data_by_id(db_session, data.ea_id) is None
