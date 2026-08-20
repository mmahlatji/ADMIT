
import uuid

from app.models.import_runs import ImportRun, ImportStatus, SourceType
from app.queries.import_run_repository import ImportRunRepository
from app.schemas.import_runs import ImportRunCreate


class ImportRunService:
    def __init__(self, importRunRepository: ImportRunRepository) -> None:
        self.repository = importRunRepository

    def get_by_id(self, import_run_id: uuid.UUID) -> ImportRun | None:
        return self.repository.get_by_id(import_run_id)

    def get_all(self) -> list[ImportRun]:
        return list(self.repository.get_all())

    def add(self, data: ImportRunCreate) -> None:
        import_run = ImportRun(
            source_type=SourceType(data.source_type),
            uploaded_by=data.uploaded_by,
            file_name=data.file_name,
            status=ImportStatus(data.status),
            rows_total=data.rows_total,
            rows_loaded=data.rows_loaded,
            rows_rejected=data.rows_rejected,
            rows_auto_matched=data.rows_auto_matched,
            rows_auto_new=data.rows_auto_new,
            rows_flagged=data.rows_flagged,
        )
        self.repository.add(import_run)
