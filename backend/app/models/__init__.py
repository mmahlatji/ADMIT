"""SQLAlchemy models, what's actually in the DB.

Includes fields that never leave the backend (e.g. password hash).
Pair each model with a schema in app/schemas.

Importing each module registers its tables on ``Base.metadata`` so Alembic
autogenerate can see them.
"""

from app.models.academic_plans import AcademicPlan
from app.models.department_codes import DepartmentCode
from app.models.applicant_marks import ApplicantMark
from app.models.applicants import Applicant
from app.models.applications import Application
from app.models.courses import Course
from app.models.import_runs import ImportRun
from app.models.matching_reviews import MatchingReview
from app.models.motivations import Motivation
from app.models.notes import Note
from app.models.staging import Staging
from app.models.system_logs import SystemLog
from app.models.users import User
from app.models.votes import Vote
from app.models.documents import Document
from .base import Base

__all__ = [
    "AcademicPlan",
    "DepartmentCode",
    "Applicant",
    "ApplicantMark",
    "Application",
    "Base",
    "Course",
    "ImportRun",
    "MatchingReview",
    "Motivation",
    "Note",
    "Staging",
    "SystemLog",
    "User",
    "Vote",
    "Document"
]