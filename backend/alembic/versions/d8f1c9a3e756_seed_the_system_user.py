"""seed the system user

Revision ID: d8f1c9a3e756
Revises: c4a71e9d8b32
Create Date: 2026-09-17 09:30:00.000000

apply_rules acts on the applicant's behalf with no human actor, and
attributes every change it makes to SYSTEM_ACTOR (employee_id "0000001",
services/engine/tools.py). system_logs.changed_by is a NOT NULL foreign
key to users.employee_id, but nothing ever created that user, so on a
database that enforces foreign keys (unlike the SQLite test fixture)
every automated decision failed the constraint and the whole run rolled
back.

role is convenor rather than left NULL: a NULL role reads as "pending
approval" everywhere in the app (queries/users.py's ordering, the People
page, the sidebar badge), so this row would sit in every convenor's
approval queue forever with nothing to actually approve. convenor matches
the authority level apply_rules already requires to be invoked at all.

The account can never sign in: users are matched to a request by the
Supabase user_id in the verified JWT's `sub` claim (services/users.py,
get_or_create_user), and no Supabase account will ever carry this row's
user_id, since it exists only in this database.

The insert is ON CONFLICT DO NOTHING on employee_id: running this against
the actual shared database turned up a row already sitting at employee_id
0000001 (first/last name "SYSTEM", email system0000001@myuct.ac.za,
created 2026-09-16), inserted by hand outside of any migration, evidently
someone else's prior workaround for this exact problem. That row already
satisfies every FK this migration exists to satisfy, so overwriting or
duplicating it would only replace one undocumented fix with another. This
migration is content to have either row present, as long as one is.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d8f1c9a3e756"
down_revision = "c4a71e9d8b32"
branch_labels = None
depends_on = None

SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"
SYSTEM_EMPLOYEE_ID = "0000001"
SYSTEM_EMAIL = "system@admit.internal"


def upgrade() -> None:
    # DO NOTHING rather than DO UPDATE: if a row is already there, something
    # else put it there for the same reason, and it is not this migration's
    # place to overwrite whatever that was.
    op.execute(
        f"""
        INSERT INTO users (user_id, employee_id, first_name, last_name, email, role, created_at)
        VALUES (
            '{SYSTEM_USER_ID}',
            '{SYSTEM_EMPLOYEE_ID}',
            'System',
            'Automated Rules',
            '{SYSTEM_EMAIL}',
            'convenor'::roles,
            now()
        )
        ON CONFLICT (employee_id) DO NOTHING
        """
    )


def downgrade() -> None:
    # Only removes the row this migration itself would have inserted (matched
    # on user_id, not just employee_id): if upgrade found someone else's row
    # already there and skipped the insert, downgrade has no business deleting
    # a row it never created. Still fails on a NOT NULL foreign key violation
    # if any system_logs row already references it, which is correct: those
    # are real automated decisions, and removing the account they are
    # attributed to would either orphan them or silently require deleting
    # them too.
    op.execute(
        f"DELETE FROM users WHERE employee_id = '{SYSTEM_EMPLOYEE_ID}' "
        f"AND user_id = '{SYSTEM_USER_ID}'"
    )
