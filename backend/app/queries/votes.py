import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.votes import Vote, VoteDecision


def get_vote_by_id(db: Session, vote_id: uuid.UUID) -> Vote | None:
    """Look up a vote by its id. Returns None if it doesn't exist yet."""
    return db.execute(select(Vote).where(Vote.vote_id == vote_id)).scalar_one_or_none()


def get_votes(db: Session, skip: int = 0, limit: int = 100) -> list[Vote]:
    """List votes, paginated."""
    return list(db.execute(select(Vote).offset(skip).order_by(Vote.voted_at.asc()).limit(limit)).scalars())


def get_votes_by_application_number(db: Session, application_number: str) -> list[Vote]:
    """List votes cast on one application, oldest first."""
    return list(
        db.execute(
            select(Vote)
            .where(Vote.application_number == application_number)
            .order_by(Vote.voted_at.asc())
        ).scalars()
    )


def get_votes_by_campus_id(db: Session, campus_id: str) -> list[Vote]:
    """List votes cast by one applicant's committee, oldest first."""
    return list(
        db.execute(
            select(Vote).where(Vote.campus_id == campus_id).order_by(Vote.voted_at.asc())
        ).scalars()
    )


def get_votes_by_application_and_voter(
    db: Session, application_number: str, voter_id: str
) -> list[Vote]:
    """This voter's votes on this application, newest first.

    A list rather than one row: the unique constraint that makes it at most
    one only arrives in a7c3e91b2f45, so rows predating it can still come back
    in pairs and asking for exactly one would raise instead of answering.
    """
    return list(
        db.execute(
            select(Vote)
            .where(
                Vote.application_number == application_number,
                Vote.voter_id == voter_id,
            )
            .order_by(Vote.voted_at.desc(), Vote.vote_id.desc())
        ).scalars()
    )


def create_vote(
    db: Session, application_number: str, campus_id: str, vote: VoteDecision, voter_id: str
) -> Vote:
    """Insert a new vote row."""
    vote_row = Vote(
        vote_id=uuid.uuid4(),
        application_number=application_number,
        campus_id=campus_id,
        vote=vote,
        voter_id=voter_id,
    )
    db.add(vote_row)
    db.flush()
    db.refresh(vote_row)
    return vote_row


def update_vote(
    db: Session,
    vote_row: Vote,
    application_number: str | None = None,
    campus_id: str | None = None,
    vote: VoteDecision | None = None,
    voter_id: str | None = None,
    voted_at: datetime | None = None,
) -> Vote:
    """Partially update a vote, only sets fields explicitly passed."""
    fields = {
        "application_number": application_number,
        "campus_id": campus_id,
        "vote": vote,
        "voter_id": voter_id,
        "voted_at": voted_at,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(vote_row, field, value)
    db.flush()
    db.refresh(vote_row)
    return vote_row


def delete_vote(db: Session, vote_row: Vote) -> None:
    """Delete a vote row."""
    db.delete(vote_row)
    db.flush()
