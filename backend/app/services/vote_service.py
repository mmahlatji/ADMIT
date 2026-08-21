
import uuid

from app.models.votes import Vote, VoteDecision
from app.queries.vote_repository import VoteRepository
from app.schemas.votes import VoteCreate


class VoteService:
    def __init__(self, vote_repository: VoteRepository) -> None:
        self.repository = vote_repository

    def get_by_id(self, vote_id: uuid.UUID) -> Vote | None:
        return self.repository.get_by_id(vote_id)

    def get_all(self) -> list[Vote]:
        return list(self.repository.get_all())

    def add(self, data: VoteCreate) -> None:
        vote = Vote(
            application_number=data.application_number,
            campus_id=data.campus_id,
            vote=VoteDecision(data.vote),
            voter_id=data.voter_id,
        )
        self.repository.add(vote)
