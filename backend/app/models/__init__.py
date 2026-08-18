"""SQLAlchemy models, what's actually in the DB.

Includes fields that never leave the backend (e.g. password hash).
Pair each model with a schema in app/schemas.

Importing each module registers its tables on ``Base.metadata`` so Alembic
autogenerate can see them.
"""

from app.deps import Base
from app.models.academic_plans import AcademicPlan
from app.models.academic_programs import AcademicProgram
from app.models.applicant_marks import ApplicantMark
from app.models.applicants import Applicant
from app.models.application_lifecycles import ApplicationLifecycle
from app.models.applications import Application
from app.models.courses import Course
from app.models.motivations import Motivation
from app.models.notes import Note
from app.models.system_logs import SystemLog
from app.models.users import User
from app.models.votes import Vote

__all__ = [
    "Base",
    "AcademicPlan",
    "AcademicProgram",
    "ApplicantMark",
    "Applicant",
    "ApplicationLifecycle",
    "Application",
    "Course",
    "Motivation",
    "Note",
    "SystemLog",
    "User",
    "Vote",
]