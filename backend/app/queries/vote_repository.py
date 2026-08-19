
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.votes import Vote


class VoteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, vote_id: uuid.UUID) -> Vote | None:
        return self.session.get(Vote, vote_id)

    def get_all(self) -> list[Vote]:
        return list(self.session.scalars(select(Vote)).all())

    def add(self, vote: Vote) -> None:
        self.session.add(vote)
        self.session.commit()

