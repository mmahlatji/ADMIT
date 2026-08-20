import uuid
from datetime import UTC, date, datetime

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
    ImportRun,
    MatchingReview,
    Motivation,
    Note,
    Staging,
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
    ImportRunCreate,
    MatchingReviewCreate,
    MotivationCreate,
    NoteCreate,
    StagingCreate,
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
    ImportRunService,
    MatchingReviewService,
    MotivationService,
    NoteService,
    StagingService,
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
        ),
        (
            ImportRunService,
            uuid.UUID("00000000-0000-0000-0000-000000000011"),
            ImportRunCreate(
                source_type="asr",
                uploaded_by="1111111",
                file_name="asr.csv",
                status="pending",
                rows_total=10,
                rows_loaded=10,
                rows_rejected=0,
                rows_auto_matched=8,
                rows_auto_new=2,
                rows_flagged=1
            ),
            ImportRun(
                import_run_id=uuid.UUID("00000000-0000-0000-0000-000000000011"),
                source_type="asr",
                uploaded_by="1111111",
                file_name="asr.csv",
                status="pending",
                rows_total=10,
                rows_loaded=10,
                rows_rejected=0,
                rows_auto_matched=8,
                rows_auto_new=2,
                rows_flagged=1
            )
        ),
        (
            MatchingReviewService,
            uuid.UUID("00000000-0000-0000-0000-000000000012"),
            MatchingReviewCreate(
                staging_row_id=uuid.UUID("00000000-0000-0000-0000-000000000013"),
                status="pending",
                resolved_by="9999999"
            ),
            MatchingReview(
                match_id=uuid.UUID("00000000-0000-0000-0000-000000000012"),
                staging_row_id=uuid.UUID("00000000-0000-0000-0000-000000000013"),
                status="pending",
                resolved_by="9999999"
            )
        ),
        (
            StagingService,
            uuid.UUID("00000000-0000-0000-0000-000000000014"),
            StagingCreate(
                import_run_id=uuid.UUID("00000000-0000-0000-0000-000000000011"),
                entity="applicants",
                raw_data={"name": "Noah", "surname": "Smith"},
                normalized_data={"first_name": "Noah", "last_name": "Smith"},
                validation_status="valid"
            ),
            Staging(
                staging_id=uuid.UUID("00000000-0000-0000-0000-000000000014"),
                import_run_id=uuid.UUID("00000000-0000-0000-0000-000000000011"),
                entity="applicants",
                raw_data={"name": "Noah", "surname": "Smith"},
                normalized_data={"first_name": "Noah", "last_name": "Smith"},
                validation_status="valid"
            )
        ),
        (
            ApplicationService,
            uuid.UUID("00000000-0000-0000-0000-000000000015"),
            ApplicationCreate(
                application_number="111111",
                campus_id="xxxyyy001",
                academic_program_code="csc",
                academic_plan1="csc01",
                academic_plan2=None,
                academic_career="hons",
                application_date=datetime(2025, 1, 15, tzinfo=UTC),
                choice="first",
                admit_type=None,
                semester="first",
                last_registration=None,
                application_term=datetime(2025, 2, 1, tzinfo=UTC),
                previous_application_term=None
            ),
            Application(
                application_id=uuid.UUID("00000000-0000-0000-0000-000000000015"),
                application_number="111111",
                campus_id="xxxyyy001",
                academic_program_code="csc",
                academic_plan1="csc01",
                academic_plan2=None,
                academic_career="hons",
                application_date=datetime(2025, 1, 15, tzinfo=UTC),
                choice="first",
                admit_type=None,
                semester="first",
                last_registration=None,
                application_term=datetime(2025, 2, 1, tzinfo=UTC),
                previous_application_term=None
            )
        ),
        (
            ApplicantService,
            uuid.UUID("00000000-0000-0000-0000-000000000016"),
            ApplicantCreate(
                campus_id="xxxyyy002",
                employee_id="2222222",
                first_name="Palesa",
                last_name="Louw",
                sex="Female",
                cell_phone="0812345678",
                home_phone="0211234567",
                email="noah@mail.net",
                population_group="African",
                birth_date=date(2000, 1, 1),
                citizenship_residency="South African",
                non_sa_citizenship=False,
                applied_for_academic_program=True
            ),
            Applicant(
                applicant_id=uuid.UUID("00000000-0000-0000-0000-000000000016"),
                campus_id="xxxyyy002",
                employee_id="2222222",
                first_name="Palesa",
                last_name="Louw",
                sex="Female",
                cell_phone="0812345678",
                home_phone="0211234567",
                email="noah@mail.net",
                population_group="African",
                birth_date=date(2000, 1, 1),
                citizenship_residency="South African",
                non_sa_citizenship=False,
                applied_for_academic_program=True
            )
        ),
        (
            ApplicationLifecycleService,
            uuid.UUID("00000000-0000-0000-0000-000000000017"),
            ApplicationLifecycleCreate(
                application_number="111111",
                program_action="placeholder",
                program_reason="placeholder",
                program_status="placeholder",
                action_processed_by="1111111"
            ),
            ApplicationLifecycle(
                application_lifecycle_id=uuid.UUID("00000000-0000-0000-0000-000000000017"),
                application_number="111111",
                program_action="placeholder",
                program_reason="placeholder",
                program_status="placeholder",
                action_processed_by="1111111"
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