"""Reconciles one wide UCT_MARKS/IT_TRANSCRIPTS row into ApplicantMark rows.

Both sources share the exact same wide shape - one row per applicant, one
column per course - so this one module covers both (see COURSE_COLUMNS in
app/adapters/columns/uct_marks.py and it_application.py).
"""

import uuid

from sqlalchemy.orm import Session

from app.queries.applicant_marks import (
    create_applicant_mark,
    get_applicant_mark_by_campus_and_course,
    update_applicant_mark,
)
from app.queries.applicants import get_applicant_by_campus_id
from app.services.imports.audit import record_change
from app.services.imports.results import MarksRowSummary

COURSE_COLUMNS = ("CSC2001F", "CSC2002F", "CSC3002F", "CSC3003F")


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
    if get_applicant_by_campus_id(db, campus_id) is None:
        return (
            MarksRowSummary(flagged=True),
            campus_id,
            f"no applicant found for campus_id {campus_id}",
        )

    summary = MarksRowSummary()
    for fact in unpivot_mark_row(row):
        existing = get_applicant_mark_by_campus_and_course(
            db, fact["campus_id"], fact["course_code"]
        )
        if existing is None:
            created = create_applicant_mark(db, **fact)
            record_change(
                db, "applicant_marks", created.mark_id, changed_by, import_run_id,
                {}, {"mark": fact["mark"]},
            )
            summary.created += 1
        elif existing.mark != fact["mark"]:
            before = {"mark": existing.mark}
            update_applicant_mark(db, existing, mark=fact["mark"])
            record_change(
                db, "applicant_marks", existing.mark_id, changed_by, import_run_id,
                before, {"mark": fact["mark"]},
            )
            summary.updated += 1
        else:
            summary.unchanged += 1

    return summary, campus_id, None
