
import uuid

from app.models.import_runs import SourceType
from app.models.staging import Staging, ValidationStatus
from app.queries.staging_repository import StagingRepository
from app.schemas.staging import StagingCreate


class StagingService:
    def __init__(self, stagingRepository: StagingRepository) -> None:
        self.repository = stagingRepository

    def get_by_id(self, staging_id: uuid.UUID) -> Staging | None:
        return self.repository.get_by_id(staging_id)

    def get_all(self) -> list[Staging]:
        return list(self.repository.get_all())

    def add(self, data: StagingCreate) -> None:
        staging = Staging(
            import_run_id=data.import_run_id,
            source_type=SourceType(data.source_type),
            raw_data=data.raw_data,
            normalized_data=data.normalized_data,
            validation_status=ValidationStatus(data.validation_status),
            rejection_reason=data.rejection_reason,
            matched_application_id=data.matched_application_id,
            matched_campus_id=data.matched_campus_id,
        )
        self.repository.add(staging)
