import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.import_runs import ImportRun, ImportStatus, SourceType


def get_import_run_by_id(db: Session, import_run_id: uuid.UUID) -> ImportRun | None:
    """Look up an import run by its id. Returns None if it doesn't exist yet."""
    return db.execute(
        select(ImportRun).where(ImportRun.import_run_id == import_run_id)
    ).scalar_one_or_none()


def get_import_runs(db: Session, skip: int = 0, limit: int = 100) -> list[ImportRun]:
    """List import runs, paginated."""
    return list(db.execute(select(ImportRun).offset(skip).order_by(ImportRun.uploaded_at.desc()).limit(limit)).scalars())


def create_import_run(
    db: Session,
    source_type: SourceType,
    uploaded_by: str,
    file_name: str,
    status: ImportStatus,
    rows_total: int,
    rows_loaded: int = 0,
    rows_rejected: int = 0,
    rows_auto_matched: int = 0,
    rows_auto_new: int = 0,
    rows_flagged: int = 0,
) -> ImportRun:
    """Insert a new import run row."""
    import_run = ImportRun(
        import_run_id=uuid.uuid4(),
        source_type=source_type,
        uploaded_by=uploaded_by,
        file_name=file_name,
        status=status,
        rows_total=rows_total,
        rows_loaded=rows_loaded,
        rows_rejected=rows_rejected,
        rows_auto_matched=rows_auto_matched,
        rows_auto_new=rows_auto_new,
        rows_flagged=rows_flagged,
    )
    db.add(import_run)
    db.flush()
    db.refresh(import_run)
    return import_run


def update_import_run(
    db: Session,
    import_run: ImportRun,
    source_type: SourceType | None = None,
    uploaded_by: str | None = None,
    file_name: str | None = None,
    status: ImportStatus | None = None,
    rows_total: int | None = None,
    rows_loaded: int | None = None,
    rows_rejected: int | None = None,
    rows_auto_matched: int | None = None,
    rows_auto_new: int | None = None,
    rows_flagged: int | None = None,
) -> ImportRun:
    """Partially update an import run, only sets fields explicitly passed."""
    fields = {
        "source_type": source_type,
        "uploaded_by": uploaded_by,
        "file_name": file_name,
        "status": status,
        "rows_total": rows_total,
        "rows_loaded": rows_loaded,
        "rows_rejected": rows_rejected,
        "rows_auto_matched": rows_auto_matched,
        "rows_auto_new": rows_auto_new,
        "rows_flagged": rows_flagged,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(import_run, field, value)
    db.flush()
    db.refresh(import_run)
    return import_run


def delete_import_run(db: Session, import_run: ImportRun) -> None:
    """Delete an import run row."""
    db.delete(import_run)
    db.flush()
