import pytest
from unittest.mock import MagicMock
from app.models import (
    AcademicPlan,
    AcademicProgram,
    Application,
    Applicant,
    ApplicantMark,
    ApplicationLifecycle,
    Course,
    Motivation,
    Note,
    SystemLog,
    User,
    Vote
)
from app.queries import (
    AcademicPlanRepository,
    AcademicProgramRepository,
    ApplicationRepository,
    ApplicantRepository,
    ApplicantMarkRepository,
    ApplicationLifecycleRepository,
    CourseRepository,
    MotivationRepository,
    NoteRepository,
    SystemLogRepository,
    UserRepository,
    VoteRepository
)

from app.schemas import (
    AcademicPlanCreate,
    AcademicProgramCreate,
    ApplicationCreate,
    ApplicantCreate,
    ApplicantMarkCreate,
    ApplicationLifecycleCreate,
    CourseCreate,
    MotivationCreate,
    NoteCreate,
    SystemLogCreate,
    UserCreate,
    VoteCreate
)

from app.services import (
    AcademicPlanService,
    AcademicProgramService,
    ApplicationService,
    ApplicantService,
    ApplicantMarkService,
    ApplicationLifecycleService,
    CourseService,
    MotivationService,
    NoteService,
    SystemLogService,
    UserService,
    VoteService
)


@pytest.mark.parametrize(
    "service, entity_id, create_schema, expected_result", 
    [
        (
            AcademicPlanService,
            1, 
            AcademicPlanCreate(academic_plan="csc06", academic_program_code="csc"),
            AcademicPlan(academic_plan_id=1, academic_plan="csc06", academic_program_code="csc"),  
        ),
        (
            MotivationService,
            "xxxyyy026",
            MotivationCreate(campus_id="xxxyyy026", first_name="Noah", last_name="Smith", motivation="Speed please, I need this, my mom is kinda homeless"),
            Motivation(campus_id="xxxyyy026", first_name="Noah", last_name="Smith", motivation="Speed please, I need this, my mom is kinda homeless")
        )
    ]
)
class TestCrudServices:
    def test_get_by_id(self, service, entity_id, create_schema, expected_result):
        mock_repo = MagicMock() # Mock the repository
        mock_servive = service(mock_repo)
        
        mock_repo.get_by_id.return_value = expected_result # Mock the expected return value
    
        result = mock_servive.get_by_id(entity_id) # call the service
    
        assert result is expected_result
        mock_repo.get_by_id.assert_called_once_with(entity_id)

    def test_get_all(self, service, entity_id, create_schema, expected_result):
        mock_repo = MagicMock()
        mock_service = service(mock_repo)
        
        mock_repo.get_all.return_value = [expected_result]

        result = mock_service.get_all()

        assert result == [expected_result]
        assert isinstance(result, list)
        mock_repo.get_all.assert_called_once()


    def test_add(self, service, entity_id, create_schema, expected_result):
        mock_repo = MagicMock()
        mock_service = service(mock_repo)
        
        mock_service.add(create_schema)

        mock_repo.add.assert_called_once()
        passed_args = mock_repo.add.call_args.args[0] # the first argument passed to the add method
    
        assert isinstance(passed_args, expected_result.__class__)