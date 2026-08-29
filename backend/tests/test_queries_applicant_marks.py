from app.queries.applicant_marks import (
    create_applicant_mark,
    delete_applicant_mark,
    get_applicant_mark_by_id,
    get_applicant_marks,
    update_applicant_mark,
)
from tests.test_queries_applicants import _create as create_applicant


def test_create_and_get_applicant_mark(db_session):
    create_applicant(db_session)
    mark = create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", "75")

    fetched = get_applicant_mark_by_id(db_session, mark.mark_id)
    assert fetched is not None
    assert fetched.mark == "75"


def test_applicant_mark_accepts_result_codes(db_session):
    create_applicant(db_session)
    mark = create_applicant_mark(db_session, "xxxyyy001", "CSC2002S", "AB")

    fetched = get_applicant_mark_by_id(db_session, mark.mark_id)
    assert fetched.mark == "AB"


def test_get_applicant_marks_returns_all(db_session):
    create_applicant(db_session)
    create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", "75")
    create_applicant_mark(db_session, "xxxyyy001", "CSC2002S", "80")

    assert len(get_applicant_marks(db_session)) == 2


def test_update_applicant_mark_only_sets_passed_fields(db_session):
    create_applicant(db_session)
    mark = create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", "75")

    updated = update_applicant_mark(db_session, mark, mark="80")
    assert updated.course_code == "CSC2001F"
    assert updated.mark == "80"


def test_delete_applicant_mark(db_session):
    create_applicant(db_session)
    mark = create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", "75")

    delete_applicant_mark(db_session, mark)

    assert get_applicant_mark_by_id(db_session, mark.mark_id) is None
