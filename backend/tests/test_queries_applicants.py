from app.models.applicants import CitizenshipResidency, SexEnum, TitleEnum
from app.queries.applicants import (
    create_applicant,
    delete_applicant,
    get_applicant_by_id,
    get_applicants,
    update_applicant,
)


def _create(db_session, campus_id="xxxyyy001", employee_id="1000001"):
    return create_applicant(
        db_session,
        campus_id=campus_id,
        employee_id=employee_id,
        title=TitleEnum.MS,
        first_name="Noah",
        last_name="Smith",
        citizenship_residency=CitizenshipResidency.SA_CITIZEN,
    )


def test_create_and_get_applicant(db_session):
    applicant = _create(db_session)

    fetched = get_applicant_by_id(db_session, applicant.applicant_id)
    assert fetched is not None
    assert fetched.campus_id == "xxxyyy001"
    assert fetched.sex is None


def test_get_applicants_returns_all(db_session):
    _create(db_session, "xxxyyy001", "1000001")
    _create(db_session, "xxxyyy002", "1000002")

    assert len(get_applicants(db_session)) == 2


def test_update_applicant_only_sets_passed_fields(db_session):
    applicant = _create(db_session)

    updated = update_applicant(db_session, applicant, sex=SexEnum.FEMALE)
    assert updated.campus_id == "xxxyyy001"
    assert updated.sex == SexEnum.FEMALE


def test_delete_applicant(db_session):
    applicant = _create(db_session)

    delete_applicant(db_session, applicant)

    assert get_applicant_by_id(db_session, applicant.applicant_id) is None
