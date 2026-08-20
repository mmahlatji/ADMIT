
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.import_runs import ImportRun


class ImportRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, import_run_id: uuid.UUID) -> ImportRun | None:
        return self.session.get(ImportRun, import_run_id)

    def get_all(self) -> list[ImportRun]:
        return list(self.session.scalars(select(ImportRun)).all())

    def add(self, import_run: ImportRun) -> None:
        self.session.add(import_run)
        self.session.commit()
