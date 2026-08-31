import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.models.applicant_marks import ResultCode
from app.models.system_logs import ChangeSource
from app.queries.applicant_marks import (
    get_applicant_mark_by_campus_and_course,
    update_applicant_mark,
)
from app.queries.system_logs import create_system_log
from app.services.imports.marks import normalize_row, reconcile_marks_row, unpivot_mark_row
from app.services.imports.results import MarksRowSummary, RowReconciliationError
from tests.test_queries_applicants import _create as create_applicant

IMPORT_RUN_ID = uuid.uuid4()
CHANGED_BY = "9999999"


def _row(**overrides):
    row = {
        "campus_id": "xxxyyy001",
        "CSC2001F": "75",
        "CSC2002S": "80",
        "CSC3002F": None,
        "CSC3003S": "",
    }
    row.update(overrides)
    return row


def test_unpivot_skips_blank_course_cells():
    facts = unpivot_mark_row(_row())

    assert facts == [
        {"campus_id": "xxxyyy001", "course_code": "CSC2001F", "mark": "75"},
        {"campus_id": "xxxyyy001", "course_code": "CSC2002S", "mark": "80"},
    ]


def test_normalize_numeric_cell_becomes_int_with_no_result_code():
    facts = normalize_row(_row(CSC2002S=None, CSC3002F=None))

    assert facts == [
        {"campus_id": "xxxyyy001", "course_code": "CSC2001F", "mark": 75, "result_code": ResultCode.NONE},
    ]


def test_normalize_result_code_cell_becomes_zero_with_code():
    facts = normalize_row(_row(CSC2001F="AB", CSC2002S=None))

    assert facts == [
        {"campus_id": "xxxyyy001", "course_code": "CSC2001F", "mark": 0, "result_code": ResultCode.AB},
    ]


def test_normalize_fail_with_mark_cell_splits_mark_and_code():
    facts = normalize_row(_row(CSC2001F="44F", CSC2002S=None))

    assert facts == [
        {"campus_id": "xxxyyy001", "course_code": "CSC2001F", "mark": 44, "result_code": ResultCode.F},
    ]


def test_normalize_bare_fail_cell_becomes_zero_with_fail_code():
    facts = normalize_row(_row(CSC2001F="F", CSC2002S=None))

    assert facts == [
        {"campus_id": "xxxyyy001", "course_code": "CSC2001F", "mark": 0, "result_code": ResultCode.F},
    ]


def test_normalize_unknown_non_numeric_cell_is_rejected():
    # used to become mark=0/NONE, which is indistinguishable from a real zero.
    # an unreadable cell is a row for a human to look at, not a score of nothing.
    with pytest.raises(RowReconciliationError):
        normalize_row(_row(CSC2001F="XYZ", CSC2002S=None))


def test_normalize_supplementary_cell_splits_mark_and_code():
    facts = normalize_row(_row(CSC2001F="47S", CSC2002S=None))

    assert facts == [
        {"campus_id": "xxxyyy001", "course_code": "CSC2001F", "mark": 47, "result_code": ResultCode.S},
    ]


def test_wide_row_creates_a_mark_per_course(db_session):
    create_applicant(db_session)

    summary, campus_id, _flag_reason = reconcile_marks_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    assert campus_id == "xxxyyy001"
    assert summary == MarksRowSummary(created=2, updated=0, unchanged=0, flagged=False)
    assert get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F").mark == 75
    assert get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2002S").mark == 80


def test_reimport_with_one_changed_value_updates_in_place(db_session):
    create_applicant(db_session)
    reconcile_marks_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())
    original_mark_id = get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F").mark_id

    summary, _, _ = reconcile_marks_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row(CSC2001F="85"))

    assert summary == MarksRowSummary(created=0, updated=1, unchanged=1, flagged=False)
    updated = get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F")
    # same row updated in place, not a duplicate - proves the unique constraint's doing its job
    assert updated.mark_id == original_mark_id
    assert updated.mark == 85


def test_unknown_campus_id_flags_the_row_without_creating_marks(db_session):
    summary, campus_id, flag_reason = reconcile_marks_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    assert campus_id == "xxxyyy001"
    assert summary == MarksRowSummary(flagged=True)
    assert flag_reason == "no applicant found for campus_id xxxyyy001"
    assert get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F") is None


def test_reimport_does_not_overwrite_manual_edit(db_session):
    create_applicant(db_session)
    reconcile_marks_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row(CSC2002S=None))
    mark = get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F")

    update_applicant_mark(db_session, mark, mark=80)
    manual_log = create_system_log(
        db_session,
        entity_name="applicant_marks",
        entity_id=mark.mark_id,
        changed_by=CHANGED_BY,
        reason=ChangeSource.MANUAL_EDIT,
        old_data={"mark": 75},
        new_data={"mark": 80},
    )
    # ensure the manual edit is the most recent log (CURRENT_TIMESTAMP is
    # second-granular on SQLite, so the import log can otherwise tie with it)
    manual_log.changed_at = datetime.now(UTC) + timedelta(days=1)
    db_session.flush()

    summary, _, _ = reconcile_marks_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row(CSC2001F="85", CSC2002S=None))

    # counted as unchanged rather than dropped: the row genuinely didn't change,
    # but leaving it uncounted made the fact vanish from the run totals
    assert summary == MarksRowSummary(created=0, updated=0, unchanged=1, flagged=False)
    assert get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F").mark == 80


def test_reimport_code_to_numeric_clears_result_code(db_session):
    create_applicant(db_session)
    reconcile_marks_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row(CSC2001F="AB"))

    mark = get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F")
    assert mark.mark == 0
    assert mark.result_code == ResultCode.AB

    summary, _, _ = reconcile_marks_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row(CSC2001F="75"))

    assert summary == MarksRowSummary(created=0, updated=1, unchanged=1, flagged=False)
    mark = get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F")
    assert mark.mark == 75
    assert mark.result_code == ResultCode.NONE


def test_supplementary_mark_keeps_its_number(db_session):
    # "46S" means scored 46 and was granted a supplementary, per the result
    # code table in the dataset README. It used to be stored as a flat 0,
    # which reads as a genuine zero.
    create_applicant(db_session)

    summary, _, _ = reconcile_marks_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY, _row(CSC2001F="46S", CSC2002S=None)
    )

    assert summary.created == 1
    mark = get_applicant_mark_by_campus_and_course(db_session, "xxxyyy001", "CSC2001F")
    assert mark.mark == 46
    assert mark.result_code == ResultCode.S


def test_unrecognized_mark_is_rejected_not_zeroed(db_session):
    # defaulting to 0 loses the distinction between "we couldn't read this"
    # and "they actually scored zero"
    create_applicant(db_session)

    with pytest.raises(RowReconciliationError):
        reconcile_marks_row(
            db_session, IMPORT_RUN_ID, CHANGED_BY, _row(CSC2001F="not-a-mark", CSC2002S=None)
        )
