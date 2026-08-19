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
            MotivationCreate(campus_id="xxxyyy026", first_name="Noah", last_name="Smith", motivation="Speed please! I need this, my mom is kinda homeless"),
            Motivation(campus_id="xxxyyy026", first_name="Noah", last_name="Smith", motivation="Speed please! I need this, my mom is kinda homeless")
        ),
        (
            AcademicProgramService,
            1,
            AcademicProgramCreate(academic_program_code="csc", academic_program="computer science honours"),
            AcademicProgram(academic_program_id=1, academic_program_code="csc", academic_program="computer science honours")
        ),
        (
            ApplicantMarkService,
            1,
            ApplicantMarkCreate(campus_id="xxxyyy001", course_code="csc2002s", mark=50),
            ApplicantMark(mark_id=1, campus_id="xxxyyy001", course_code="csc2002s", mark=50)
        ),
        (
            CourseService,
            1, 
            CourseCreate(academic_program_code="csc05", course_code="csc2002s", course_name="CS 2002s"),
            Course(course_id=1, academic_program_code="csc05", course_code="csc2002s", course_name="CS 2002s")
        ),
        (
            NoteService,
            1,
            NoteCreate(campus_id="xxxyyy001", author_id="9999999", content="Student seems capable"),
            Note(note_id=1, campus_id="xxxyyy001", author_id="9999999", content="Student seems capable")
        ),
        (
            VoteService,
            1,
            VoteCreate(application_number="111111", campus_id="xxxyyy001", vote="placeholder", voter_id="9999999"),
            Vote(vote_id=1, application_number="111111", campus_id="xxxyyy001", vote="placeholder", voter_id="9999999")
        ),
        (
            UserService,
            "1111111",
            UserCreate(employee_id="1111111", first_name="Palesa", last_name="Louw", email="palesa@mail.net", role=None),
            User(employee_id="1111111", first_name="Palesa", last_name="Louw", email="palesa@mail.net", role=None)
        ),
        (
            SystemLogService,
            1,
            SystemLogCreate(
                entity_name="applicant_marks",
                entity_id="xxxyyy001", 
                old_data={
                    "mark_id": 1,
                    "campus_id": "xxxyyy001",
                    "course_code": "csc2002s",
                    "mark": 50
                },
                new_data={
                    "mark_id": 1,
                    "campus_id": "xxxyyy001",
                    "course_code": "csc2002s",
                    "mark": 90
                },
                changed_by="111111",
                reason="manual_edit"
            ),
            SystemLog(
                log_id=1,
                entity_name="applicant_marks",
                entity_id="xxxyyy001", 
                old_data={
                    "mark_id": 1,
                    "campus_id": "xxxyyy001",
                    "course_code": "csc2002s",
                    "mark": 50
                },
                new_data={
                    "mark_id": 1,
                    "campus_id": "xxxyyy001",
                    "course_code": "csc2002s",
                    "mark": 90
                },
                changed_by="111111",
                reason="manual_edit"
            )
        )


    ]
)
class TestCrudServices:                             # DO NOT CHANGE THE UNUSED PARAMETERS 
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