import uuid

from sqlalchemy.orm import Session

from app.models.import_runs import ImportRun, ImportStatus, SourceType
from app.queries import import_runs as import_queries


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
    if uploaded_by.strip() == "":
        raise ValueError("Cannot create a note without an employee id")
    import_run = import_queries.create_import_run(
        db, 
        source_type, 
        uploaded_by, 
        file_name, 
        status,
        rows_total,
        rows_loaded,
        rows_rejected,
        rows_auto_matched,
        rows_auto_new,
        rows_flagged
    )
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
    import_run = import_queries.update_import_run(
        db, 
        import_run, 
        source_type, 
        uploaded_by, 
        file_name, 
        status,
        rows_total,
        rows_loaded,
        rows_rejected,
        rows_auto_matched,
        rows_auto_new,
        rows_flagged
        )
    return import_run


def list_import_runs(db: Session, skip: int = 0, limit: int = 100) -> list[ImportRun]:
    return import_queries.get_import_runs(db, skip, limit)


def get_import_run_by_id(db: Session, import_run_id: uuid.UUID) -> ImportRun | None:
    return import_queries.get_import_run_by_id(db, import_run_id)