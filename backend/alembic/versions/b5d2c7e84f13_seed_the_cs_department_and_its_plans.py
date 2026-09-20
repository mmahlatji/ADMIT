"""seed the cs department and its academic plans

Revision ID: b5d2c7e84f13
Revises: a7c3e91b2f45
Create Date: 2026-09-19 15:00:00.000000

An ASR row is rejected outright when its department is unknown. The importer
takes the department from the plan code (characters 5 to 8, so SH001CSC05 is
CSC) and asks academic_plans what that department's internal and external
plans are; resolve_plans returning None raises "Unknown department" and the
row never lands. On a database where nobody has inserted these by hand, that
is every row of every ASR sheet, and the failure names the department rather
than the missing reference data, so it reads like a bad sheet.

Same reasoning as d8f1c9a3e756 and the system user: the application cannot
work without these rows, so they belong in the migrations rather than in
whatever someone typed into the shared database once.

Which plan is which matters. compute_incorrect_and_requires_plan_change_flags
puts UCT students on the internal plan and everyone else on the external one,
and flags the application when they are on the wrong side. Getting these two
the wrong way round would not fail, it would silently flag the entire intake
backwards.

The plan_type labels are 'Internal' and 'External', not the 'INTERNAL' and
'EXTERNAL' the initial schema created: f65e730dde7d renamed every enum label
to match its value.

Both inserts are ON CONFLICT DO NOTHING. The shared database already carries
these rows, added by hand before this existed, so there this migration does
nothing at all. It is for the next database, not that one.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b5d2c7e84f13"
down_revision = "a7c3e91b2f45"
branch_labels = None
depends_on = None

DEPARTMENT_ID = "00000000-0000-0000-0000-00000000c5c0"
DEPARTMENT_CODE = "CSC"

INTERNAL_PLAN_ID = "00000000-0000-0000-0000-00000000c5c5"
INTERNAL_PLAN = "SH001CSC05"

EXTERNAL_PLAN_ID = "00000000-0000-0000-0000-00000000c5c6"
EXTERNAL_PLAN = "SH001CSC06"


def upgrade() -> None:
    op.execute(
        f"""
        INSERT INTO departments (department_id, department_code, department_name)
        VALUES ('{DEPARTMENT_ID}', '{DEPARTMENT_CODE}', 'Computer Science')
        ON CONFLICT (department_code) DO NOTHING
        """
    )
    # After the department: academic_plans.department_code is a foreign key to it.
    op.execute(
        f"""
        INSERT INTO academic_plans (academic_plan_id, department_code, academic_plan, plan_type)
        VALUES
            ('{INTERNAL_PLAN_ID}', '{DEPARTMENT_CODE}', '{INTERNAL_PLAN}', 'Internal'::academic_plan_type),
            ('{EXTERNAL_PLAN_ID}', '{DEPARTMENT_CODE}', '{EXTERNAL_PLAN}', 'External'::academic_plan_type)
        ON CONFLICT (academic_plan) DO NOTHING
        """
    )


def downgrade() -> None:
    # Matched on id as well as code, so a row this migration found already
    # present and skipped is not one it then deletes. Plans before the
    # department they point at.
    op.execute(
        f"DELETE FROM academic_plans WHERE academic_plan_id IN "
        f"('{INTERNAL_PLAN_ID}', '{EXTERNAL_PLAN_ID}')"
    )
    op.execute(
        f"DELETE FROM departments WHERE department_id = '{DEPARTMENT_ID}' "
        f"AND department_code = '{DEPARTMENT_CODE}'"
    )
