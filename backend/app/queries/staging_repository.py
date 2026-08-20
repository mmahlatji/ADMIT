
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.staging import Staging


class StagingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, staging_id: uuid.UUID) -> Staging | None:
        return self.session.get(Staging, staging_id)

    def get_all(self) -> list[Staging]:
        return list(self.session.scalars(select(Staging)).all())

    def add(self, staging: Staging) -> None:
        self.session.add(staging)
        self.session.commit()
