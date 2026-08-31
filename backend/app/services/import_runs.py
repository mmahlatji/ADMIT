from sqlalchemy.orm import Session

from app.models.import_runs import ImportRun, ImportStatus, SourceType
from app.queries import import_runs as import_queries


def get_import_run_by_source_type(db: Session, source_type: SourceType) -> ImportRun | None:
    return import_queries.get_pending_import_run_by_source_type(db, source_type)


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