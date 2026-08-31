import uuid

from app.queries.applicant_marks import get_applicant_mark_by_campus_and_course
from app.services.imports.marks import reconcile_marks_row, unpivot_mark_row
from app.services.imports.results import MarksRowSummary
from tests.test_queries_applicants import _create as create_applicant

IMPORT_RUN_ID = uuid.uuid4()
CHANGED_BY = "9999999"


def _row(**overrides):
    row = {
        "campus_id": "xxxyyy001",
        "CSC2001F": "75",
        "CSC2002F": "80",
        "CSC3002F": None,
        "CSC3003F": "",
    }
    row.update(overrides)
    return row


def test_unpivot_skips_blank_course_cells():
    facts = unpivot_mark_row(_row())

    assert facts == [
        {"campus_id": "xxxyyy001", "course_code": "CSC2001F", "mark": "75"},
        {"campus_id": "xxxyyy001", "course_code": "CSC2002F", "mark": "80"},
    ]


def test_wide_row_creates_a_mark_per_course(db_session):
    create_applicant(db_session)

    summary, campus_id, flag_reason = reconcile_marks_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    assert campus_id == "xxxyyy001"
    assert summary == MarksRowSummary(created=2, updated=0, unchanged=0, flagged=False)
    assert get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F").mark == "75"
    assert get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2002F").mark == "80"


def test_reimport_with_one_changed_value_updates_in_place(db_session):
    create_applicant(db_session)
    reconcile_marks_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())
    original_mark_id = get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F").mark_id

    summary, _, _ = reconcile_marks_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row(CSC2001F="85"))

    assert summary == MarksRowSummary(created=0, updated=1, unchanged=1, flagged=False)
    updated = get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F")
    # same row updated in place, not a duplicate - proves the unique constraint's doing its job
    assert updated.mark_id == original_mark_id
    assert updated.mark == "85"


def test_unknown_campus_id_flags_the_row_without_creating_marks(db_session):
    summary, campus_id, flag_reason = reconcile_marks_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    assert campus_id == "xxxyyy001"
    assert summary == MarksRowSummary(flagged=True)
    assert flag_reason == "no applicant found for campus_id xxxyyy001"
    assert get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F") is None
