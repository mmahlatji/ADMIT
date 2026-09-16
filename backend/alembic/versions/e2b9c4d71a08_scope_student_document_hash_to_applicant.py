"""scope the student document hash uniqueness to the applicant

Revision ID: e2b9c4d71a08
Revises: f65e730dde7d
Create Date: 2026-09-15 16:40:00.000000

sha256_hash was unique across the whole table, so the second applicant to
upload a byte-identical file was refused and their document was never stored.
Uniqueness belongs on the pair: the same bytes may appear once per applicant.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e2b9c4d71a08"
down_revision = "f65e730dde7d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "student_documents_sha256_hash_key", "student_documents", type_="unique"
    )
    op.create_unique_constraint(
        "uq_student_document_applicant_hash",
        "student_documents",
        ["applicant_id", "sha256_hash"],
    )


def downgrade() -> None:
    # Only reversible while no two applicants share a hash. Once the wider
    # constraint has let such a pair in, restoring the global one fails, which
    # is the correct outcome: it would otherwise mean deleting a real document.
    op.drop_constraint(
        "uq_student_document_applicant_hash", "student_documents", type_="unique"
    )
    op.create_unique_constraint(
        "student_documents_sha256_hash_key", "student_documents", ["sha256_hash"]
    )
