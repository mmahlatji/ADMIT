
import uuid

from app.models.matching_reviews import MatchingReview, MatchResolution, MatchStatus
from app.queries.matching_review_repository import MatchingReviewRepository
from app.schemas.matching_reviews import MatchingReviewCreate


class MatchingReviewService:
    def __init__(self, matching_review_repository: MatchingReviewRepository) -> None:
        self.repository = matching_review_repository

    def get_by_id(self, match_id: uuid.UUID) -> MatchingReview | None:
        return self.repository.get_by_id(match_id)

    def get_all(self) -> list[MatchingReview]:
        return list(self.repository.get_all())

    def add(self, data: MatchingReviewCreate) -> None:
        matching_review = MatchingReview(
            staging_row_id=data.staging_row_id,
            candidate_keys=data.candidate_keys,
            match_signals=data.match_signals,
            status=MatchStatus(data.status),
            resolved_by=data.resolved_by,
            resolution=MatchResolution(data.resolution) if data.resolution is not None else None,
            reason=data.reason,
        )
        self.repository.add(matching_review)
