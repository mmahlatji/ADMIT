
import uuid

from app.models.application_lifecycles import (
    ApplicationLifecycle,
    ProgramAction,
    ProgramReason,
    ProgramStatus,
)
from app.queries.application_lifecycle_repository import ApplicationLifecycleRepository
from app.schemas.application_lifecycles import ApplicationLifecycleCreate


class ApplicationLifecycleService:
    def __init__(self, application_lifecycle_repository: ApplicationLifecycleRepository) -> None:
        self.repository = application_lifecycle_repository

    def get_by_id(self, application_lifecycle_id: uuid.UUID) -> ApplicationLifecycle | None:
        return self.repository.get_by_id(application_lifecycle_id)

    def get_all(self) -> list[ApplicationLifecycle]:
        return list(self.repository.get_all())

    def add(self, data: ApplicationLifecycleCreate) -> None:
        lifecycle = ApplicationLifecycle(
            application_number=data.application_number,
            program_action=ProgramAction(data.program_action),
            program_reason=ProgramReason(data.program_reason),
            program_status=ProgramStatus(data.program_status),
            action_processed_by=data.action_processed_by,
        )
        self.repository.add(lifecycle)
