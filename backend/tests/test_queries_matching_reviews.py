from datetime import UTC, datetime

from app.models.matching_reviews import MatchResolution, MatchStatus
from app.queries.matching_reviews import (
    create_matching_review,
    delete_matching_review,
    get_matching_review_by_id,
    get_matching_reviews,
    update_matching_review,
)
from tests.test_queries_staging import _create as create_staging_row


def _create(db_session):
    staging = create_staging_row(db_session)
    return create_matching_review(db_session, staging.staging_id, MatchStatus.PENDING)


def test_create_and_get_matching_review(db_session):
    review = _create(db_session)

    fetched = get_matching_review_by_id(db_session, review.match_id)
    assert fetched is not None
    assert fetched.status == MatchStatus.PENDING
    assert fetched.resolved_at is None


def test_get_matching_reviews_returns_all(db_session):
    staging = create_staging_row(db_session)
    create_matching_review(db_session, staging.staging_id, MatchStatus.PENDING)
    create_matching_review(db_session, staging.staging_id, MatchStatus.PENDING)

    assert len(get_matching_reviews(db_session)) == 2


def test_update_matching_review_sets_resolved_at_explicitly(db_session):
    review = _create(db_session)
    resolved_at = datetime.now(UTC)

    updated = update_matching_review(
        db_session,
        review,
        status=MatchStatus.RESOLVED,
        resolution=MatchResolution.MERGE,
        resolved_by="9999999",
        resolved_at=resolved_at,
    )
    assert updated.status == MatchStatus.RESOLVED
    # the value we set, tz intact. This used to come back naive because the
    # query helper re-read it from SQLite, which drops tzinfo; the column is
    # DateTime(timezone=True) so postgres always kept it.
    assert updated.resolved_at == resolved_at


def test_delete_matching_review(db_session):
    review = _create(db_session)

    delete_matching_review(db_session, review)

    assert get_matching_review_by_id(db_session, review.match_id) is None
