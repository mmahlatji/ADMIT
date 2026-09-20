from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.votes import Vote, VoteDecision
from app.queries import applications as appl_queries
from app.queries import votes as vote_queries


class ApplicationNotFoundError(Exception):
    """Raised when a vote references an application that doesn't exist."""


def list_votes(
    db: Session,
    application_number: str | None = None,
    campus_id: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Vote]:
    if application_number is not None:
        return vote_queries.get_votes_by_application_number(db, application_number)
    if campus_id is not None:
        return vote_queries.get_votes_by_campus_id(db, campus_id)
    return vote_queries.get_votes(db, skip, limit)


def create_vote(
    db: Session,
    actor,
    application_number: str,
    vote: VoteDecision,
) -> Vote:
    application = appl_queries.get_application_by_number(db, application_number)
    if application is None:
        raise ApplicationNotFoundError(application_number)
    # One vote each per application, which is what the committee screen says.
    # Casting again replaces your own vote rather than adding a second row,
    # and clears any duplicates left behind from before that was enforced.
    existing = vote_queries.get_votes_by_application_and_voter(
        db, application_number, actor.employee_id
    )
    if existing:
        current, *stale = existing
        for duplicate in stale:
            vote_queries.delete_vote(db, duplicate)
        return vote_queries.update_vote(
            db, current, vote=vote, voted_at=datetime.now(UTC)
        )
    return vote_queries.create_vote(
        db,
        application_number=application_number,
        campus_id=application.campus_id,
        vote=vote,
        voter_id=actor.employee_id,
    )
