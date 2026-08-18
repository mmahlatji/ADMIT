
from app.models.system_logs import ChangeSource, SystemLog
from app.queries.system_log_repository import SystemLogRepository
from app.schemas.system_logs import SystemLogCreate


class SystemLogService:
    def __init__(self, systemLogRepository: SystemLogRepository) -> None:
        self.repository = systemLogRepository

    def get_by_id(self, log_id: int) -> SystemLog | None:
        return self.repository.get_by_id(log_id)

    def get_all(self) -> list[SystemLog]:
        return list(self.repository.get_all())

    def add(self, data: SystemLogCreate) -> None:
        system_log = SystemLog(
            entity_name=data.entity_name,
            entity_id=data.entity_id,
            old_data=data.old_data,
            new_data=data.new_data,
            changed_by=data.changed_by,
            reason=ChangeSource(data.reason),
            import_run_id=data.import_run_id,
        )
        self.repository.add(system_log)
