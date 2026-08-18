
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.motivations import Motivation


class MotivationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, campus_id: str) -> Motivation | None:
        return self.session.get(Motivation, campus_id)

    def get_all(self) -> list[Motivation]:
        return list(self.session.scalars(select(Motivation)).all())

    def add(self, motivation: Motivation) -> None:
        self.session.add(motivation)
        self.session.commit()

