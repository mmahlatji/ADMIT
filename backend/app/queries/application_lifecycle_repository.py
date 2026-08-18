
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application_lifecycles import ApplicationLifecycle


class ApplicationLifecycleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, application_number: str) -> ApplicationLifecycle | None:
        return self.session.get(ApplicationLifecycle, application_number)

    def get_all(self) -> list[ApplicationLifecycle]:
        return list(self.session.scalars(select(ApplicationLifecycle)).all())

    def add(self, application_lifecycle: ApplicationLifecycle) -> None:
        self.session.add(application_lifecycle)
        self.session.commit()

