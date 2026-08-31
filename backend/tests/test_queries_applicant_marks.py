import pytest
from sqlalchemy.exc import IntegrityError

from app.models.applicant_marks import ResultCode
from app.queries.applicant_marks import (
    create_applicant_mark,
    delete_applicant_mark,
    get_applicant_mark_by_campus_and_course,
    get_applicant_mark_by_id,
    get_applicant_marks,
    update_applicant_mark,
)
from tests.test_queries_applicants import _create as create_applicant


def test_create_and_get_applicant_mark(db_session):
    create_applicant(db_session)
    mark = create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", 75, ResultCode.NONE)

    fetched = get_applicant_mark_by_id(db_session, mark.mark_id)
    assert fetched is not None
    assert fetched.mark == 75


def test_applicant_mark_accepts_result_codes(db_session):
    create_applicant(db_session)
    mark = create_applicant_mark(db_session, "xxxyyy001", "CSC2002S", 0, ResultCode.AB)

    fetched = get_applicant_mark_by_id(db_session, mark.mark_id)
    assert fetched.mark == 0
    assert fetched.result_code == ResultCode.AB


def test_get_applicant_marks_returns_all(db_session):
    create_applicant(db_session)
    create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", 75, ResultCode.NONE)
    create_applicant_mark(db_session, "xxxyyy001", "CSC2002S", 80, ResultCode.NONE)

    assert len(get_applicant_marks(db_session)) == 2


def test_update_applicant_mark_only_sets_passed_fields(db_session):
    create_applicant(db_session)
    mark = create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", 75, ResultCode.NONE)

    updated = update_applicant_mark(db_session, mark, mark=80)
    assert updated.course_code == "CSC2001F"
    assert updated.mark == 80


def test_update_applicant_mark_sets_result_code(db_session):
    create_applicant(db_session)
    mark = create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", 75, ResultCode.NONE)

    updated = update_applicant_mark(db_session, mark, result_code=ResultCode.DE)
    assert updated.mark == 75
    assert updated.result_code == ResultCode.DE


def test_update_applicant_mark_sets_result_code_to_none(db_session):
    create_applicant(db_session)
    mark = create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", 0, ResultCode.AB)

    updated = update_applicant_mark(db_session, mark, result_code=ResultCode.NONE)
    assert updated.mark == 0
    assert updated.result_code == ResultCode.NONE


def test_delete_applicant_mark(db_session):
    create_applicant(db_session)
    mark = create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", 75, ResultCode.NONE)

    delete_applicant_mark(db_session, mark)

    assert get_applicant_mark_by_id(db_session, mark.mark_id) is None


def test_get_applicant_mark_by_campus_and_course(db_session):
    create_applicant(db_session)
    create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", 75, ResultCode.NONE)

    found = get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F")
    assert found is not None
    assert found.mark == 75
    assert get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC9999X") is None


def test_duplicate_campus_course_raises_integrity_error(db_session):
    # proves the uq_applicant_marks_campus_id_course_code constraint is enforced,
    # which is what makes a re-import update an existing mark instead of duplicating it
    create_applicant(db_session)
    create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", 75, ResultCode.NONE)

    with pytest.raises(IntegrityError):
        create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", 75, ResultCode.NONE)
