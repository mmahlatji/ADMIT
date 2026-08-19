
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.system_logs import SystemLog


class SystemLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, log_id: uuid.UUID) -> SystemLog | None:
        return self.session.get(SystemLog, log_id)

    def get_all(self) -> list[SystemLog]:
        return list(self.session.scalars(select(SystemLog)).all())

    def add(self, system_log: SystemLog) -> None:
        self.session.add(system_log)
        self.session.commit()

