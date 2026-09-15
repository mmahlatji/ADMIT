"""align enum labels with values, add rules.rule_action

Revision ID: f65e730dde7d
Revises: b1ad82133dca
Create Date: 2026-09-10 23:26:17.879122

Nine enum columns gained ``values_callable``, so SQLAlchemy now writes each
member's value, not its name. The types were created from the names, so the
labels are renamed to match. ``RENAME VALUE`` is a catalogue-only change and
existing rows read back under the new label, so it is safe on populated tables.

``semester`` also gains ``unspecified`` (in the model, never migrated),
``vote_decision`` is rebuilt from its placeholder-only type (votes is empty),
and ``rules.rule_action`` is added NOT NULL with existing rows backfilled ACCEPT.
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "f65e730dde7d"
down_revision = "b1ad82133dca"
branch_labels = None
depends_on = None


# old (name) -> new (value) for every enum that gained values_callable and whose
# value differs from its member name.
LABEL_RENAMES = {
    "title_enum": [
        ("MR", "Mr"),
        ("MS", "Ms"),
        ("MISS", "Miss"),
        ("UNSPECIFIED", "Unspecified"),
    ],
    "sex_enum": [
        ("MALE", "M"),
        ("FEMALE", "F"),
    ],
    "citizenship_residency": [
        ("SA_CITIZEN", "SA Citizen"),
        ("INTERNATIONAL", "International"),
        ("PERMANENT_RESIDENT", "Permanent Resident"),
    ],
    "academic_plan_type": [
        ("INTERNAL", "Internal"),
        ("EXTERNAL", "External"),
    ],
    "choice": [
        ("FIRST", "FRST"),
        ("SECOND", "SCND"),
    ],
    "semester": [
        ("FIRST", "1st Semester"),
        ("SECOND", "2nd Semester"),
    ],
    "application_status": [
        ("APPLIED", "Applied"),
        ("REVIEWED", "Reviewed"),
        ("CONDITIONAL_OFFER", "Conditional Offer"),
        ("ACCEPTED", "Accepted"),
        ("READY_TO_REGISTER", "Ready to Register"),
        ("DENIED", "Denied"),
        ("CANCELLED", "Cancelled"),
    ],
    "deny_reson": [
        ("NOT_COMPETITIVE", "Not competitive"),
        ("REQUIREMENTS_NOT_MET", "Requirements not met"),
        ("DUPLICATE_APPLICATION", "Duplicate application"),
        ("INCORRECT_PROGRAM", "Incorrect program"),
    ],
}


def _rename_values(pairs):
    for type_name, renames in pairs.items():
        for old, new in renames:
            op.execute(
                f"ALTER TYPE {type_name} RENAME VALUE '{old}' TO '{new}'"
            )


def upgrade() -> None:
    _rename_values(LABEL_RENAMES)

    # model has Semester.UNSPECIFIED = "unspecified"; the type never had it
    op.execute("ALTER TYPE semester ADD VALUE IF NOT EXISTS 'unspecified'")

    # vote_decision shipped as a single 'PLACEHOLDER' label. votes is empty, so
    # swap the type for the real one rather than leaving the placeholder behind.
    op.execute("ALTER TYPE vote_decision RENAME TO vote_decision_old")
    vote_decision = postgresql.ENUM("yes", "no", "abstain", name="vote_decision")
    vote_decision.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE votes ALTER COLUMN vote TYPE vote_decision "
        "USING vote::text::vote_decision"
    )
    op.execute("DROP TYPE vote_decision_old")

    # new NOT NULL column. RuleAction has no values_callable, so the labels are
    # the member names. server_default backfills existing rules, then is dropped
    # because the model declares no default.
    rule_action = postgresql.ENUM("REJECT", "ACCEPT", name="rule_action")
    rule_action.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE rules ADD COLUMN rule_action rule_action "
        "NOT NULL DEFAULT 'ACCEPT'"
    )
    op.execute("ALTER TABLE rules ALTER COLUMN rule_action DROP DEFAULT")

    op.create_table(
        "saved_queries",
        sa.Column("query_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("spec", sa.JSON, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("query_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"])
    )
    op.create_index(
        op.f("ix_saved_queries_user_id"),
        "saved_queries",
        ["user_id"],
        unique=False
    )

    op.create_index(
        op.f("ix_saved_queries_created_at"),
        "saved_queries",
        ["created_at"],
        unique=False
    )


def downgrade() -> None:
    op.execute("ALTER TABLE rules DROP COLUMN rule_action")
    op.execute("DROP TYPE rule_action")

    op.execute("ALTER TYPE vote_decision RENAME TO vote_decision_old")
    vote_decision = postgresql.ENUM("PLACEHOLDER", name="vote_decision")
    vote_decision.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE votes ALTER COLUMN vote TYPE vote_decision "
        "USING vote::text::vote_decision"
    )
    op.execute("DROP TYPE vote_decision_old")

    # Postgres cannot drop a value from an enum, so rebuild semester without
    # 'unspecified'. The FIRST/SECOND labels are restored here rather than
    # through the rename loop below; 'unspecified' rows (the column is nullable)
    # go back to NULL.
    op.execute("ALTER TYPE semester RENAME TO semester_old")
    op.execute("CREATE TYPE semester AS ENUM ('FIRST', 'SECOND')")
    op.execute(
        "ALTER TABLE applications ALTER COLUMN semester TYPE semester USING ("
        "CASE semester::text "
        "WHEN '1st Semester' THEN 'FIRST' "
        "WHEN '2nd Semester' THEN 'SECOND' "
        "END)::semester"
    )
    op.execute("DROP TYPE semester_old")

    reverse = {
        type_name: [(new, old) for old, new in renames]
        for type_name, renames in LABEL_RENAMES.items()
        if type_name != "semester"
    }
    _rename_values(reverse)
    
    op.drop_index(op.f("ix_saved_queries_user_id"), table_name="saved_queries")
    op.drop_index(op.f("ix_saved_queries_created_at"), table_name="saved_queries")
    op.drop_table("saved_queries")
    

