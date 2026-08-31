"""Reconciles one MOTIVATIONS row into a Motivation, 1:1 with an Applicant."""

import uuid

from sqlalchemy.orm import Session

from app.queries.motivations import (
    create_motivation,
    update_motivation,
)
from app.services.imports import lookups
from app.services.imports.audit import record_change
from app.services.imports.results import ReconcileOutcome


def reconcile_motivation_row(
    db: Session, import_run_id: uuid.UUID, changed_by: str, row: dict
) -> tuple[ReconcileOutcome, str, str | None]:
    """Upsert the Motivation for one applicant.

    Returns (outcome, matched_campus_id, flag_reason); flag_reason is None
    unless the row was skipped for manual matching.

    The motivations sheet only carries campus_id + text (no name), so
    first_name/last_name are backfilled from the matched Applicant, never from
    the sheet.
    """
    campus_id = row["campus_id"]
    applicant = lookups.applicant_by_campus_id(db, campus_id)
    if applicant is None:
        return (
            ReconcileOutcome.SKIPPED_UNMATCHED,
            campus_id,
            f"no applicant found for campus_id {campus_id}",
        )

    motivation_text = row.get("motivation")
    existing = lookups.motivation_by_campus_id(db, campus_id)

    if existing is None:
        created = create_motivation(
            db,
            campus_id=campus_id,
            first_name=applicant.first_name,
            last_name=applicant.last_name,
            motivation=motivation_text,
        )
        lookups.remember_motivation(db, created)
        record_change(
            db, "motivations", created.motivation_id, changed_by, import_run_id,
            {}, {"motivation": motivation_text},
        )
        return ReconcileOutcome.CREATED, campus_id, None

    # read the value actually written, not the intended one: update_motivation
    # treats motivation=None as "leave it alone", not "clear it", so a blank
    # incoming row never actually changes an existing motivation - diffing the
    # real before/after (instead of assuming the write took) keeps the audit
    # log honest about that
    before = existing.motivation
    update_motivation(db, existing, motivation=motivation_text)
    after = existing.motivation
    if before == after:
        return ReconcileOutcome.UNCHANGED, campus_id, None

    record_change(
        db, "motivations", existing.motivation_id, changed_by, import_run_id,
        {"motivation": before}, {"motivation": after},
    )
    return ReconcileOutcome.UPDATED, campus_id, None
