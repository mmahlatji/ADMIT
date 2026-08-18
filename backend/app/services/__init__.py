"""All real logic lives here: ingestion, matching, field-level merge
precedence, the rules engine, lifecycle transitions. Plain Python, no
HTTP awareness, testable with plain pytest.
"""
from .academic_plan_service import AcademicPlanService
from .academic_program_service import AcademicProgramService
from .applicant_mark_service import ApplicantMarkService
from .applicant_service import ApplicantService
from .application_lifecycle_service import ApplicationLifecycleService
from .application_service import ApplicationService
from .course_service import CourseService
from .motivation_service import MotivationService
from .note_service import NoteService
from .system_log_service import SystemLogService
from .user_service import UserService
from .vote_service import VoteService

__all__ = [
    "AcademicPlanService",
    "AcademicProgramService",
    "ApplicantMarkService",
    "ApplicantService",
    "ApplicationLifecycleService",
    "ApplicationService",
    "CourseService",
    "MotivationService",
    "NoteService",
    "SystemLogService",
    "UserService",
    "VoteService",
]