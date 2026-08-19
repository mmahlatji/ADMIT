import uuid

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
            uuid.UUID("00000000-0000-0000-0000-000000000001"),
            AcademicPlanCreate(academic_plan="csc06", academic_program_code="csc"),
            AcademicPlan(academic_plan_id=uuid.UUID("00000000-0000-0000-0000-000000000001"), academic_plan="csc06", academic_program_code="csc"),
        ),
        (
            MotivationService,
            uuid.UUID("00000000-0000-0000-0000-000000000002"),
            MotivationCreate(campus_id="xxxyyy026", first_name="Noah", last_name="Smith", motivation="Speed please! I need this, my mom is kinda homeless"),
            Motivation(motivation_id=uuid.UUID("00000000-0000-0000-0000-000000000002"), campus_id="xxxyyy026", first_name="Noah", last_name="Smith", motivation="Speed please! I need this, my mom is kinda homeless")
        ),
        (
            AcademicProgramService,
            uuid.UUID("00000000-0000-0000-0000-000000000003"),
            AcademicProgramCreate(academic_program_code="csc", academic_program="computer science honours"),
            AcademicProgram(academic_program_id=uuid.UUID("00000000-0000-0000-0000-000000000003"), academic_program_code="csc", academic_program="computer science honours")
        ),
        (
            ApplicantMarkService,
            uuid.UUID("00000000-0000-0000-0000-000000000004"),
            ApplicantMarkCreate(campus_id="xxxyyy001", course_code="csc2002s", mark=50),
            ApplicantMark(mark_id=uuid.UUID("00000000-0000-0000-0000-000000000004"), campus_id="xxxyyy001", course_code="csc2002s", mark=50)
        ),
        (
            CourseService,
            uuid.UUID("00000000-0000-0000-0000-000000000005"),
            CourseCreate(academic_program_code="csc05", course_code="csc2002s", course_name="CS 2002s"),
            Course(course_id=uuid.UUID("00000000-0000-0000-0000-000000000005"), academic_program_code="csc05", course_code="csc2002s", course_name="CS 2002s")
        ),
        (
            NoteService,
            uuid.UUID("00000000-0000-0000-0000-000000000006"),
            NoteCreate(campus_id="xxxyyy001", author_id="9999999", content="Student seems capable"),
            Note(note_id=uuid.UUID("00000000-0000-0000-0000-000000000006"), campus_id="xxxyyy001", author_id="9999999", content="Student seems capable")
        ),
        (
            VoteService,
            uuid.UUID("00000000-0000-0000-0000-000000000007"),
            VoteCreate(application_number="111111", campus_id="xxxyyy001", vote="placeholder", voter_id="9999999"),
            Vote(vote_id=uuid.UUID("00000000-0000-0000-0000-000000000007"), application_number="111111", campus_id="xxxyyy001", vote="placeholder", voter_id="9999999")
        ),
        (
            UserService,
            uuid.UUID("00000000-0000-0000-0000-000000000008"),
            UserCreate(employee_id="1111111", first_name="Palesa", last_name="Louw", email="palesa@mail.net", role=None),
            User(user_id=uuid.UUID("00000000-0000-0000-0000-000000000008"), employee_id="1111111", first_name="Palesa", last_name="Louw", email="palesa@mail.net", role=None)
        ),
        (
            SystemLogService,
            uuid.UUID("00000000-0000-0000-0000-000000000009"),
            SystemLogCreate(
                entity_name="applicant_marks",
                entity_id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
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
                log_id=uuid.UUID("00000000-0000-0000-0000-000000000009"),
                entity_name="applicant_marks",
                entity_id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
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