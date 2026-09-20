"""one vote per voter per application

Revision ID: a7c3e91b2f45
Revises: f3a2b8c1d904
Create Date: 2026-09-19 10:00:00.000000

The committee screen has always said "one vote each per application", but
nothing enforced it: casting again inserted a second row rather than
replacing the first, so a voter who changed their mind was counted twice
and the tally on the applicant page was wrong.

The service now upserts. This adds the constraint that makes that the only
possible shape, after collapsing the duplicates already on the database
down to each voter's most recent vote on each application.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a7c3e91b2f45"
down_revision = "f3a2b8c1d904"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Keep the latest vote per (application, voter). vote_id breaks ties so
    # this is deterministic even if two rows share a timestamp.
    op.execute(
        """
        DELETE FROM votes older
        USING votes newer
        WHERE older.application_number = newer.application_number
          AND older.voter_id = newer.voter_id
          AND (
                older.voted_at < newer.voted_at
                OR (older.voted_at = newer.voted_at AND older.vote_id < newer.vote_id)
          )
        """
    )
    op.create_unique_constraint(
        "uq_vote_application_voter", "votes", ["application_number", "voter_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_vote_application_voter", "votes", type_="unique")
