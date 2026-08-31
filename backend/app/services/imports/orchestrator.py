"""Runs one uploaded sheet through its adapter and reconciles the result into
the database. This is the piece that connects the two halves that already
existed separately: the adapter pipeline (app/adapters/) and the staging/
import-run persistence layer (app/models/staging.py, app/models/import_runs.py).
"""

import uuid

import pandas as pd
from sqlalchemy.orm import Session

from app.adapters.asr import ASRAdapter
from app.adapters.base import BaseAdapter
from app.adapters.exceptions import AdapterValidationError
from app.adapters.it_application import ITApplicationAdapter
from app.adapters.motivations import MotivationsAdapter
from app.adapters.uct_marks import UCTMarkAdapter
from app.models.import_runs import ImportRun, ImportStatus, SourceType
from app.models.matching_reviews import MatchStatus
from app.models.staging import ValidationStatus
from app.queries.import_runs import create_import_run, update_import_run
from app.queries.matching_reviews import create_matching_review
from app.services.imports.asr import reconcile_asr_row
from app.services.imports.marks import reconcile_marks_row
from app.services.imports.motivations import reconcile_motivation_row
from app.services.imports.results import (
    MarksRowSummary,
    ReconcileOutcome,
    RowReconciliationError,
    RunCounters,
)
from app.services.imports.staging import stage_row, to_json_safe
from app.services.imports.value_mapping import clean_cell

_ADAPTER_BY_SOURCE: dict[SourceType, type[BaseAdapter]] = {
    SourceType.ASR: ASRAdapter,
    SourceType.UCT_MARKS: UCTMarkAdapter,
    SourceType.IT_TRANSCRIPTS: ITApplicationAdapter,
    SourceType.MOTIVATIONS: MotivationsAdapter,
}


def _dispatch(
    source_type: SourceType, db: Session, import_run_id: uuid.UUID, changed_by: str, row: dict
) -> tuple[ReconcileOutcome | MarksRowSummary, str | None, str | None, str | None]:
    """Send one normalized row to the right reconciler and normalize the
    return shape to (outcome_or_summary, matched_campus_id,
    matched_application_id, flag_reason).
    """
    if source_type is SourceType.ASR:
        outcome, campus_id, application_number, flag_reason = reconcile_asr_row(
            db, import_run_id, changed_by, row
        )
        return outcome, campus_id, application_number, flag_reason
    if source_type in (SourceType.UCT_MARKS, SourceType.IT_TRANSCRIPTS):
        summary, campus_id, flag_reason = reconcile_marks_row(db, import_run_id, changed_by, row)
        return summary, campus_id, None, flag_reason
    if source_type is SourceType.MOTIVATIONS:
        outcome, campus_id, flag_reason = reconcile_motivation_row(db, import_run_id, changed_by, row)
        return outcome, campus_id, None, flag_reason
    raise ValueError(f"no reconciler wired up for source_type {source_type}")


def run_import(
    db: Session, source_type: SourceType, uploaded_by: str, file_name: str, sheet: pd.DataFrame
) -> ImportRun:
    """Run one uploaded sheet through its adapter and reconcile it into the DB.

    Runs synchronously - there's no queue/worker yet, so this returns once the
    whole sheet has been processed, with status already COMPLETED or FAILED.
    Every row (clean or needs-review) lands in Staging regardless of outcome,
    tied to the one ImportRun this call creates. Outcomes that are skipped are
    loaded into the matching review table with the reasons for skipping.
    """
    import_run = create_import_run(
        db,
        source_type=source_type,
        uploaded_by=uploaded_by,
        file_name=file_name,
        status=ImportStatus.PROCESSING,
        rows_total=len(sheet),
    )

    adapter = _ADAPTER_BY_SOURCE[source_type](sheet)
    try:
        clean_df, needs_review_df, _violations = adapter.process()
    except AdapterValidationError:
        return update_import_run(db, import_run, status=ImportStatus.FAILED)

    entity_tag = source_type.value
    counters = RunCounters()

    # column-validation failures: staged as REJECTED, never reach reconciliation
    for idx in needs_review_df.index:
        raw = to_json_safe(needs_review_df.loc[idx].to_dict())
        normalized = to_json_safe(
            adapter.format_for_database(needs_review_df.loc[[idx]]).iloc[0].to_dict()
        )
        stage_row(
            db, import_run.import_run_id, entity_tag, raw, normalized,
            ValidationStatus.REJECTED, rejection_reason="failed column validation",
        )
        counters.rows_rejected += 1

    # clean rows: staged either way, and reconciled into the final tables
    reverse_output_columns = {
        db_col: enum_col.value for enum_col, db_col in adapter.output_columns.items()
    }
    # commit the staging
    db.commit()

    for idx in clean_df.index:
        # reconciliation gets the row as pandas produced it (pd.Timestamp etc,
        # which SQLAlchemy/SQLite accept fine) - only the copy going into
        # Staging needs to be JSON-safe. Passing the JSON-safe copy into
        # reconciliation instead used to stringify dates before they ever
        # reached a Date column, crashing every ASR row with a date field.
        # NaN/NaT (a blank cell) must still become None, though: SQLAlchemy's
        # Date/String types reject float('nan').
        
        row = {
            key: clean_cell(value)
            for key, value in clean_df.loc[idx].to_dict().items()
        }
        normalized = to_json_safe(row)
        raw = to_json_safe(clean_df.loc[idx].rename(reverse_output_columns).to_dict())
        try:
            with db.begin_nested():
                outcome, matched_campus_id, matched_application_id, flag_reason = _dispatch(
                    source_type, db, import_run.import_run_id, uploaded_by, row
                )
        except RowReconciliationError as exc:
            stage_row(
                db, import_run.import_run_id, entity_tag, raw, normalized,
                ValidationStatus.REJECTED, rejection_reason=str(exc),
            )
            counters.rows_rejected += 1
            continue

        flagged = outcome is ReconcileOutcome.SKIPPED_UNMATCHED or (
            isinstance(outcome, MarksRowSummary) and outcome.flagged
        )
        staged = stage_row(
            db, import_run.import_run_id, entity_tag, raw, normalized,
            ValidationStatus.PENDING if flagged else ValidationStatus.VALID,
            rejection_reason=flag_reason,
            matched_campus_id=matched_campus_id,
            matched_application_id=matched_application_id,
        )
        if flagged:
            create_matching_review(
                db,
                staging_row_id=staged.staging_id,
                status=MatchStatus.PENDING,
                reason=flag_reason,
            )
        if isinstance(outcome, MarksRowSummary):
            counters.add_marks_summary(outcome)
        else:
            counters.add_outcome(outcome)
    db.commit()

    return update_import_run(
        db,
        import_run,
        status=ImportStatus.COMPLETED,
        rows_rejected=counters.rows_rejected,
        rows_loaded=counters.rows_loaded,
        rows_auto_matched=counters.rows_auto_matched,
        rows_auto_new=counters.rows_auto_new,
        rows_flagged=counters.rows_flagged,
    )
