import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.matching_reviews import MatchingReview, MatchResolution, MatchStatus
from app.models.staging import Staging


def get_matching_review_by_id(db: Session, match_id: uuid.UUID) -> MatchingReview | None:
    """Look up a matching review by its id. Returns None if it doesn't exist yet."""
    return db.execute(
        select(MatchingReview).where(MatchingReview.match_id == match_id)
    ).scalar_one_or_none()


def get_matching_reviews(db: Session, skip: int = 0, limit: int = 100) -> list[MatchingReview]:
    """List matching reviews, paginated."""
    return list(db.execute(select(MatchingReview).offset(skip).order_by(MatchingReview.match_id.asc()).limit(limit)).scalars())


def get_matching_reviews_by_status(
    db: Session, status: MatchStatus, skip: int = 0, limit: int = 100
) -> list[MatchingReview]:
    """List matching reviews filtered by status, paginated."""
    return list(
        db.execute(
            select(MatchingReview)
            .where(MatchingReview.status == status)
            .order_by(MatchingReview.match_id.asc())
            .offset(skip)
            .limit(limit)
        ).scalars()
    )


def create_matching_review(
    db: Session,
    staging_row_id: uuid.UUID,
    status: MatchStatus,
    candidate_keys: dict[str, Any] | None = None,
    match_signals: dict[str, Any] | None = None,
    resolved_by: str | None = None,
    resolution: MatchResolution | None = None,
    reason: str | None = None,
) -> MatchingReview:
    """Insert a new matching review row."""
    review = MatchingReview(
        match_id=uuid.uuid4(),
        staging_row_id=staging_row_id,
        status=status,
        candidate_keys=candidate_keys,
        match_signals=match_signals,
        resolved_by=resolved_by,
        resolution=resolution,
        reason=reason,
    )
    db.add(review)
    db.flush()
    return review


def update_matching_review(
    db: Session,
    review: MatchingReview,
    staging_row_id: uuid.UUID | None = None,
    status: MatchStatus | None = None,
    candidate_keys: dict[str, Any] | None = None,
    match_signals: dict[str, Any] | None = None,
    resolved_by: str | None = None,
    resolution: MatchResolution | None = None,
    reason: str | None = None,
    resolved_at: datetime | None = None,
) -> MatchingReview:
    """Partially update a matching review, only sets fields explicitly passed.

    resolved_at is a plain optional kwarg here rather than something the db infers
    (e.g. via onupdate), so whichever service resolves a review sets it explicitly.
    """
    fields = {
        "staging_row_id": staging_row_id,
        "status": status,
        "candidate_keys": candidate_keys,
        "match_signals": match_signals,
        "resolved_by": resolved_by,
        "resolution": resolution,
        "reason": reason,
        "resolved_at": resolved_at,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(review, field, value)
    db.flush()
    return review


def delete_matching_review(db: Session, review: MatchingReview) -> None:
    """Delete a matching review row."""
    db.delete(review)
    db.flush()


def get_open_review_for(
    db: Session,
    *,
    reason: str | None,
    matched_campus_id: str | None,
    matched_application_id: str | None,
) -> MatchingReview | None:
    """Find an unresolved review already raised for the same thing.

    Reviews hang off a staging row, and every import writes fresh staging rows,
    so without this the same unchanged problem is re-raised on every import and
    the queue fills with duplicates of work nobody has done yet. Matching on the
    staging row's matched keys plus the reason identifies "this same complaint
    about this same record". Only PENDING counts: once someone resolves one, a
    later recurrence is genuinely new and should be raised again.
    """
    if matched_campus_id is None and matched_application_id is None:
        return None
    return db.execute(
        select(MatchingReview)
        .join(Staging, Staging.staging_id == MatchingReview.staging_row_id)
        .where(
            MatchingReview.status == MatchStatus.PENDING,
            MatchingReview.reason == reason,
            Staging.matched_campus_id == matched_campus_id,
            Staging.matched_application_id == matched_application_id,
        )
        .limit(1)
    ).scalar_one_or_none()
