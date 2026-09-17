"""merge the orphaned uppercase semester label

Revision ID: f3a2b8c1d904
Revises: d8f1c9a3e756
Create Date: 2026-09-18 10:00:00.000000

The semester type on this database already carried an 'UNSPECIFIED' label
before f65e730dde7d ever ran, added outside of any migration in this
history (the initial schema only ever creates FIRST/SECOND). That
migration's `ALTER TYPE semester ADD VALUE IF NOT EXISTS 'unspecified'`
assumed the lowercase value was genuinely new, so it added a second,
separate label instead of renaming the one that was already there. Every
row that had semester = 'UNSPECIFIED' (391 of 392 application rows on
this database) was left pointing at a label the model can no longer
read, since Semester only defines FIRST, SECOND and unspecified.

Rebuilt the same way f65e730dde7d's own downgrade already rebuilds this
type (Postgres cannot drop or merge enum labels in place): rename the
old type aside, create the correct one, cast the column across with a
CASE that folds both 'UNSPECIFIED' and 'unspecified' onto the single
lowercase label, then drop the old type.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f3a2b8c1d904"
down_revision = "d8f1c9a3e756"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE semester RENAME TO semester_old")
    op.execute("CREATE TYPE semester AS ENUM ('1st Semester', '2nd Semester', 'unspecified')")
    op.execute(
        "ALTER TABLE applications ALTER COLUMN semester TYPE semester USING ("
        "CASE semester::text "
        "WHEN 'UNSPECIFIED' THEN 'unspecified' "
        "WHEN 'unspecified' THEN 'unspecified' "
        "WHEN '1st Semester' THEN '1st Semester' "
        "WHEN '2nd Semester' THEN '2nd Semester' "
        "END)::semester"
    )
    op.execute("DROP TYPE semester_old")


def downgrade() -> None:
    # Deliberately refuses rather than pretending: this merges two labels
    # that meant the same thing into one, so once applied there is no record
    # of which rows used to say 'UNSPECIFIED' versus 'unspecified'. Restoring
    # the old label on the type would not restore the old data, so a
    # downgrade here would silently lie about what it did.
    raise NotImplementedError(
        "This migration merges data and cannot be reversed. Restore from a "
        "backup taken before it ran if you need the pre-merge state back."
    )
