"""Pydantic schemas, what's allowed over the wire, shaped per audience/role.

Never the same class as the matching SQLAlchemy model in app/models.
"""
from .academic_plans import AcademicPlanCreate
from .academic_programs import AcademicProgramCreate
from .applicant_marks import ApplicantMarkCreate
from .applicants import ApplicantCreate
from .application_lifecycles import ApplicationLifecycleCreate
from .applications import ApplicationCreate
from .courses import CourseCreate
from .import_runs import ImportRunCreate
from .matching_reviews import MatchingReviewCreate
from .motivations import MotivationCreate
from .notes import NoteCreate
from .staging import StagingCreate
from .system_logs import SystemLogCreate
from .users import UserCreate
from .votes import VoteCreate

__all__ = [
    "AcademicPlanCreate",
    "AcademicProgramCreate",
    "ApplicantMarkCreate",
    "ApplicantCreate",
    "ApplicationLifecycleCreate",
    "ApplicationCreate",
    "CourseCreate",
    "ImportRunCreate",
    "MatchingReviewCreate",
    "MotivationCreate",
    "NoteCreate",
    "StagingCreate",
    "SystemLogCreate",
    "UserCreate",
    "VoteCreate",
]