"""Thin wrapper around the staging-table queries, plus JSON-safety for the
pandas values that come straight out of an adapter.
"""

import uuid
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.models.staging import Staging, ValidationStatus
from app.queries.staging import create_staging_row


def to_json_safe(row: dict[str, Any]) -> dict[str, Any]:
    """Replace pandas NaN/NaT with None and stringify timestamps.

    Staging.raw_data/normalized_data are NOT NULL JSON columns - a bare NaN or
    a pandas Timestamp isn't valid JSON, so this has to happen before a row is
    staged, not after.
    """
    cleaned: dict[str, Any] = {}
    for key, value in row.items():
        if pd.isna(value):
            cleaned[key] = None
        elif hasattr(value, "isoformat"):
            cleaned[key] = value.isoformat()
        else:
            cleaned[key] = value
    return cleaned


def stage_row(
    db: Session,
    import_run_id: uuid.UUID,
    entity: str,
    raw: dict[str, Any],
    normalized: dict[str, Any],
    status: ValidationStatus,
    rejection_reason: str | None = None,
    matched_campus_id: str | None = None,
    matched_application_id: str | None = None,
) -> Staging:
    """Record one row of an import run in the staging table, for audit purposes.

    Every row lands here regardless of whether it went on to change anything -
    staging is the append-only log of what was actually received, not the
    source of truth for current data.
    """
    return create_staging_row(
        db,
        import_run_id=import_run_id,
        entity=entity,
        raw_data=to_json_safe(raw),
        normalized_data=to_json_safe(normalized),
        validation_status=status,
        rejection_reason=rejection_reason,
        matched_campus_id=matched_campus_id,
        matched_application_id=matched_application_id,
    )
