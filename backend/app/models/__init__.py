"""SQLAlchemy models, what's actually in the DB.

Includes fields that never leave the backend (e.g. password hash).
Pair each model with a schema in app/schemas.

Importing each module registers its tables on ``Base.metadata`` so Alembic
autogenerate can see them.
"""

from app.models.academic_plans import AcademicPlan
from app.models.applicant_marks import ApplicantMark
from app.models.applicants import Applicant
from app.models.applications import Application
from app.models.courses import Course
from app.models.departments import Department
from app.models.external_applicants_data import ExternalApplicantData
from app.models.import_documents import Document
from app.models.import_runs import ImportRun
from app.models.matching_reviews import MatchingReview
from app.models.motivations import Motivation
from app.models.notes import Note

# without this import Rules never registers on Base.metadata, so create_all
# skips the table and alembic autogenerate can't see it either
from app.models.rules import Rules
from app.models.saved_queries import SavedQuery
from app.models.staging import Staging
from app.models.student_documents import StudentDocument
from app.models.system_logs import SystemLog
from app.models.users import User
from app.models.votes import Vote

from .base import Base

__all__ = [
    "AcademicPlan",
    "Applicant",
    "ApplicantMark",
    "Application",
    "Base",
    "Course",
    "Department",
    "Document",
    "ExternalApplicantData",
    "ImportRun",
    "MatchingReview",
    "Motivation",
    "Note",
    "Rules",
    "SavedQuery",
    "Staging",
    "StudentDocument",
    "SystemLog",
    "User",
    "Vote"
]