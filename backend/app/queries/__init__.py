"""SQLAlchemy queries, grouped by what they query (by table/aggregate).

No business logic here, services call these, never the other way round.
"""
from .academic_plan_repository import AcademicPlanRepository
from .academic_program_repository  import AcademicProgramRepository
from .applicant_mark_repository  import ApplicantMarkRepository
from .applicant_repository import ApplicantRepository
from .application_lifecycle_repository  import ApplicationLifecycleRepository
from .application_repository import ApplicationRepository
from .course_repository import CourseRepository
from .motivation_repository import MotivationRepository
from .note_repository import NoteRepository
from .system_log_repository import SystemLogRepository
from .user_repository import UserRepository
from .vote_repository import VoteRepository

__all__ = [
    "AcademicPlanRepository",
    "AcademicProgramRepository",
    "ApplicantMarkRepository",
    "ApplicantRepository",
    "ApplicationLifecycleRepository",
    "ApplicationRepository",
    "CourseRepository",
    "MotivationRepository",
    "NoteRepository",
    "SystemLogRepository",
    "UserRepository",
    "VoteRepository",
]