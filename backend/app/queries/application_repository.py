
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.applications import Application


class ApplicationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, application_number: str) -> Application | None:
        return self.session.get(Application, application_number)

    def get_all(self) -> list[Application]:
        return list(self.session.scalars(select(Application)).all())

    def add(self, application: Application) -> None:
        self.session.add(application)
        self.session.commit()

