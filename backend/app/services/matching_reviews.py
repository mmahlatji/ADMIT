import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.matching_reviews import MatchResolution, MatchStatus
from app.models.system_logs import ChangeSource
from app.queries import matching_reviews as match_queries
from app.queries import system_logs as system_log_queries


def list_reviews(db: Session, status: MatchStatus | None = None, skip: int = 0, limit: int = 100):
    if status is not None:
        return match_queries.get_matching_reviews_by_status(db, status, skip, limit)
    return match_queries.get_matching_reviews(db, skip, limit)


def get_review_by_id(db: Session, match_id: uuid.UUID):
    return match_queries.get_matching_review_by_id(db, match_id)


def resolve_review(
    db: Session,
    actor,
    review,
    resolution: MatchResolution,
    reason: str | None = None,
):
    """Record the resolution of a matching review. Does not merge data."""
    previous_status = review.status
    previous_resolution = review.resolution
    review = match_queries.update_matching_review(
        db,
        review,
        status=MatchStatus.RESOLVED,
        resolution=resolution,
        reason=reason,
        resolved_by=actor.employee_id,
        resolved_at=datetime.now(UTC),
    )
    system_log_queries.create_system_log(
        db,
        entity_name="matching_reviews",
        entity_id=review.match_id,
        changed_by=actor.employee_id,
        reason=ChangeSource.MERGE_RESOLUTION,
        old_data={
            "status": previous_status.value,
            "resolution": previous_resolution.value if previous_resolution else None,
        },
        new_data={"status": MatchStatus.RESOLVED.value, "resolution": resolution.value},
    )
    return review
