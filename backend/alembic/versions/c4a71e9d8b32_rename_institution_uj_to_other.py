"""rename institution UJ to OTHER

Revision ID: c4a71e9d8b32
Revises: e2b9c4d71a08
Create Date: 2026-09-15 14:10:00.000000

rules.rule_action arrives in f65e730dde7d, which added it independently on
main, so this only carries the Institution rename. Chained onto
e2b9c4d71a08 so the branch stays a single linear head after merging main.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c4a71e9d8b32"
down_revision = "e2b9c4d71a08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # RENAME VALUE rather than a new type: UJ was only ever a stand-in for "not
    # UCT", and renaming leaves existing rows and the
    # uq_rule_institution_year_version constraint alone. Institution has no
    # values_callable, so the labels are the member names.
    op.execute("ALTER TYPE institution RENAME VALUE 'UJ' TO 'OTHER'")


def downgrade() -> None:
    op.execute("ALTER TYPE institution RENAME VALUE 'OTHER' TO 'UJ'")
