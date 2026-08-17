"""SQLAlchemy models, what's actually in the DB.

Includes fields that never leave the backend (e.g. password hash).
Pair each model with a schema in app/schemas.

Importing each module registers its tables on ``Base.metadata`` so Alembic
autogenerate can see them.
"""

from app.models import (  # noqa: F401
    academic_plans,
    academic_programs,
    applicant_marks,
    applicants,
    application_lifecycles,
    applications,
    courses,
    motivations,
    notes,
    system_logs,
    users,
    votes,
)

from app.deps import Base

__all__ = ["Base"]
