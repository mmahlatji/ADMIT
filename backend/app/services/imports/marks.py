"""Reconciles one wide UCT_MARKS/IT_TRANSCRIPTS row into ApplicantMark rows.

Both sources share the exact same wide shape - one row per applicant, one
column per course - so this one module covers both (see COURSE_COLUMNS in
app/adapters/columns/uct_marks.py and it_application.py).
"""

import uuid

from sqlalchemy.orm import Session

from app.models.applicant_marks import ResultCode
from app.models.system_logs import ChangeSource
from app.queries.applicant_marks import (
    create_applicant_mark,
    update_applicant_mark,
)
from app.services.imports import lookups
from app.services.imports.audit import record_change
from app.services.imports.results import MarksRowSummary, RowReconciliationError
from app.services.system_logs import get_latest_log_by_entity_and_entity_id

COURSE_COLUMNS = ("CSC2001F", "CSC2002S", "CSC3002F", "CSC3003S")

# bare codes: no numeric mark was released for the course at all
_COURSE_RESULT_CODE = {
    "OSS": ResultCode.OSS,
    "PA": ResultCode.PA,
    "DE": ResultCode.DE,
    "AB": ResultCode.AB,
    "F" : ResultCode.F
}

# NN<letter> cells, where the number IS the mark and the letter says what
# happened to it: "44F" failed with 44, "47S" scored 47 and was granted a
# supplementary. See the result code table in the dataset README.
_MARK_SUFFIX_CODE = {
    "F": ResultCode.F,
    "S": ResultCode.S,
}



def unpivot_mark_row(row: dict) -> list[dict]:
    """Turn one wide {campus_id, CSC2001F, CSC2002F, ...} row into one dict per
    course that actually has a value.

    A blank/missing course cell just isn't a fact yet, not a mark of "nothing" -
    it's skipped rather than written as an empty mark.
    """
    campus_id = row["campus_id"]
    facts = []
    for course_code in COURSE_COLUMNS:
        value = row.get(course_code)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            continue
        facts.append({"campus_id": campus_id, "course_code": course_code, "mark": str(value).strip()})
    return facts

def normalize_row(row: dict) -> list[dict]:
    """
        If the mark cell is none numeric then default the mark
        to zero and place the code e.g. OSS in the ResultCode
        field
    """
    facts = unpivot_mark_row(row)
    for fact in facts:
        value = fact["mark"]

        if value.isdigit():
            fact["mark"] = int(value)
            fact["result_code"] = ResultCode.NONE
            continue

        bare_code = _COURSE_RESULT_CODE.get(value.upper())
        if bare_code is not None:
            fact["mark"] = 0
            fact["result_code"] = bare_code
            continue

        # "44F" / "47S": keep the number, the suffix records what became of it.
        # Only F was handled before, so a granted supplementary like "46S" fell
        # through and was stored as 0, which reads as a genuine zero.
        suffix_code = _MARK_SUFFIX_CODE.get(value[-1:].upper())
        prefix = value[:-1]
        if suffix_code is not None and prefix.isdigit():
            fact["mark"] = int(prefix)
            fact["result_code"] = suffix_code
            continue

        # anything else is a value nobody has taught this code about. Flagging
        # beats defaulting to 0, which is indistinguishable from a real zero.
        raise RowReconciliationError(
            f"unrecognized mark {value!r} for {fact['course_code']}"
        )
    return facts


def reconcile_marks_row(
    db: Session, import_run_id: uuid.UUID, changed_by: str, row: dict
) -> tuple[MarksRowSummary, str, str | None]:
    """Upsert every mark fact in one wide row.

    Returns (summary, matched_campus_id, flag_reason); flag_reason is None
    unless the row was flagged for manual matching.

    The applicant is looked up once for the whole row, not once per course, so
    an unknown campus_id flags the row a single time rather than up to 4 times.
    """
    campus_id = row["campus_id"]
    if lookups.applicant_by_campus_id(db, campus_id) is None:
        return (
            MarksRowSummary(flagged=True),
            campus_id,
            f"no applicant found for campus_id {campus_id}",
        )

    summary = MarksRowSummary()
    for fact in normalize_row(row):
        existing = lookups.mark_by_campus_and_course(
            db, fact["campus_id"], fact["course_code"]
        )
        if existing is None:
            created = create_applicant_mark(db, **fact)
            lookups.remember_mark(db, created)
            record_change(
                db, "applicant_marks", created.mark_id, changed_by, import_run_id,
                {}, {"mark": fact["mark"], "result_code": fact["result_code"]},
            )
            summary.created += 1
        elif existing.mark != fact["mark"] or existing.result_code != fact["result_code"]:
            latest_log = get_latest_log_by_entity_and_entity_id(db, "applicant_marks", existing.mark_id)
            if latest_log is None or latest_log.reason != ChangeSource.MANUAL_EDIT: # Protect manual edits
                before = {"mark": existing.mark, "result_code": existing.result_code}
                update_applicant_mark(db, existing, mark=fact["mark"], result_code=fact["result_code"])
                record_change(
                    db, "applicant_marks", existing.mark_id, changed_by, import_run_id,
                    before, {"mark": fact["mark"], "result_code": fact["result_code"]},
                )
                summary.updated += 1
            else:
                # a manual edit won: the row is left alone, but it still has to
                # be counted or the fact silently vanishes from the run totals
                summary.unchanged += 1
        else:
            summary.unchanged += 1

    return summary, campus_id, None
