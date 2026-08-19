
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.applications import Application


class ApplicationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, application_id: uuid.UUID) -> Application | None:
        return self.session.get(Application, application_id)

    def get_all(self) -> list[Application]:
        return list(self.session.scalars(select(Application)).all())

    def add(self, application: Application) -> None:
        self.session.add(application)
        self.session.commit()

