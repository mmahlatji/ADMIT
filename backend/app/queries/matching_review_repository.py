
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.matching_reviews import MatchingReview


class MatchingReviewRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, match_id: uuid.UUID) -> MatchingReview | None:
        return self.session.get(MatchingReview, match_id)

    def get_all(self) -> list[MatchingReview]:
        return list(self.session.scalars(select(MatchingReview)).all())

    def add(self, matching_review: MatchingReview) -> None:
        self.session.add(matching_review)
        self.session.commit()
