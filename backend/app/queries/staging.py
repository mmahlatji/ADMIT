import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.staging import Staging, ValidationStatus


def get_staging_by_id(db: Session, staging_id: uuid.UUID) -> Staging | None:
    """Look up a staging row by its id. Returns None if it doesn't exist yet."""
    return db.execute(select(Staging).where(Staging.staging_id == staging_id)).scalar_one_or_none()


def get_staging_rows(db: Session, skip: int = 0, limit: int = 100) -> list[Staging]:
    """List staging rows, paginated."""
    return list(db.execute(select(Staging).offset(skip).limit(limit)).scalars())


def create_staging_row(
    db: Session,
    import_run_id: uuid.UUID,
    entity: str,
    raw_data: dict[str, Any],
    normalized_data: dict[str, Any],
    validation_status: ValidationStatus,
    rejection_reason: str | None = None,
    matched_application_id: str | None = None,
    matched_campus_id: str | None = None,
) -> Staging:
    """Insert a new staging row."""
    staging = Staging(
        staging_id=uuid.uuid4(),
        import_run_id=import_run_id,
        entity=entity,
        raw_data=raw_data,
        normalized_data=normalized_data,
        validation_status=validation_status,
        rejection_reason=rejection_reason,
        matched_application_id=matched_application_id,
        matched_campus_id=matched_campus_id,
    )
    db.add(staging)
    db.flush()
    db.refresh(staging)
    return staging


def update_staging_row(
    db: Session,
    staging: Staging,
    import_run_id: uuid.UUID | None = None,
    entity: str | None = None,
    raw_data: dict[str, Any] | None = None,
    normalized_data: dict[str, Any] | None = None,
    validation_status: ValidationStatus | None = None,
    rejection_reason: str | None = None,
    matched_application_id: str | None = None,
    matched_campus_id: str | None = None,
) -> Staging:
    """Partially update a staging row, only sets fields explicitly passed."""
    fields = {
        "import_run_id": import_run_id,
        "entity": entity,
        "raw_data": raw_data,
        "normalized_data": normalized_data,
        "validation_status": validation_status,
        "rejection_reason": rejection_reason,
        "matched_application_id": matched_application_id,
        "matched_campus_id": matched_campus_id,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(staging, field, value)
    db.flush()
    db.refresh(staging)
    return staging


def delete_staging_row(db: Session, staging: Staging) -> None:
    """Delete a staging row."""
    db.delete(staging)
    db.flush()
