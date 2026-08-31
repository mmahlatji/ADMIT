import pandas as pd

from app.models.academic_plans import AcademicPlanType
from app.models.import_runs import ImportStatus, SourceType
from app.models.matching_reviews import MatchStatus
from app.models.staging import ValidationStatus
from app.queries.academic_plans import create_academic_plan
from app.queries.applicants import get_applicant_by_campus_id
from app.queries.matching_reviews import get_matching_reviews
from app.queries.staging import get_staging_rows
from app.services.imports.orchestrator import run_import
from tests.test_queries_notes import _create_author

UPLOADED_BY = "9999999"


def _seed_plans(db_session):
    create_academic_plan(db_session, "CSC", "SH001CSC05", AcademicPlanType.INTERNAL)
    create_academic_plan(db_session, "CSC", "SH001CSC06", AcademicPlanType.EXTERNAL)


def _asr_sheet(rows: int = 1) -> pd.DataFrame:
    # one full, valid ASR row - every ASRInputColumn member needs a value here,
    # see tests/test_adapters.py's valid_sheet fixture for the same convention
    base = {
        "Application Number": "100001",
        "Campus Id": "123456",
        "Employee Id": "EMP001",
        "Academic Program Code": "CSC",
        "Title": "Ms",
        "Sex": "F",
        "Academic Plan 1": "SH001CSC05",
        "Academic Plan 2": None,
        "Academic Career": "hons",
        "Application Date": pd.Timestamp("2026-01-15"),
        "Choice": "first",
        "Admit Type": "regular",
        "Semester": "first",
        "Last Registration": "1:2026:2",  # real ASR data uses a colon-delimited string here, not a date
        "Application Term": pd.Timestamp("2026-01-01"),
        "Previous Application Term": None,
        "First Name": "Noah",
        "Last Name": "Smith",
        "Cell Phone": "0821234567",
        "Home Phone": "0211234567",
        "Email Address": "noah@example.com",
        "Population Group": "African",
        "Birth Date": pd.Timestamp("2000-01-01"),
        "Citizenship Residency": "SA Citizen",
        "Non SA Citizenship": None,
        "Effective Date": pd.Timestamp("2026-01-15"),
        "Program Action": "DDEF",
        "Program Reason": "HOD",
        "Program Status": "Applicant",
    }
    return pd.DataFrame([base] * rows)


def test_fresh_import_completes_with_accurate_counters(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    sheet = _asr_sheet(rows=1)

    import_run = run_import(db_session, SourceType.ASR, UPLOADED_BY, "asr.xlsx", sheet)

    assert import_run.status == ImportStatus.COMPLETED
    assert import_run.rows_total == 1
    assert import_run.rows_loaded == 1
    assert import_run.rows_auto_new == 1
    assert import_run.rows_auto_matched == 0
    assert import_run.rows_rejected == 0
    assert get_applicant_by_campus_id(db_session, "123456") is not None


def test_needs_review_rows_are_staged_rejected_and_excluded_from_reconciliation(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    sheet = _asr_sheet(rows=2)
    sheet.loc[1, "Employee Id"] = None  # fails the EMPLOYEE_ID NON_NULL critical rule

    import_run = run_import(db_session, SourceType.ASR, UPLOADED_BY, "asr.xlsx", sheet)

    assert import_run.status == ImportStatus.COMPLETED
    assert import_run.rows_total == 2
    assert import_run.rows_loaded == 1
    assert import_run.rows_rejected == 1

    staging_rows = get_staging_rows(db_session)
    assert len(staging_rows) == 2
    statuses = {row.validation_status for row in staging_rows}
    assert statuses == {ValidationStatus.VALID, ValidationStatus.REJECTED}


def test_sheet_missing_required_columns_fails_the_whole_run(db_session):
    _create_author(db_session)
    sheet = _asr_sheet(rows=1).drop(columns=["Campus Id"])

    import_run = run_import(db_session, SourceType.ASR, UPLOADED_BY, "asr.xlsx", sheet)

    assert import_run.status == ImportStatus.FAILED
    assert get_staging_rows(db_session) == []


def _marks_sheet(rows: int = 1) -> pd.DataFrame:
    base = {
        "Student ID": "UNKNOWN1",
        "CSC2001F": "75",
        "CSC2002F": None,
        "CSC3002F": None,
        "CSC3003F": None,
    }
    return pd.DataFrame([base] * rows)


def test_flagged_marks_row_opens_matching_review(db_session):
    _create_author(db_session)
    sheet = _marks_sheet(rows=1)

    import_run = run_import(db_session, SourceType.UCT_MARKS, UPLOADED_BY, "marks.csv", sheet)

    assert import_run.status == ImportStatus.COMPLETED

    staging_rows = get_staging_rows(db_session)
    assert len(staging_rows) == 1
    staging = staging_rows[0]
    assert staging.validation_status == ValidationStatus.PENDING
    assert "no applicant found for campus_id UNKNOWN1" in staging.rejection_reason

    reviews = get_matching_reviews(db_session)
    assert len(reviews) == 1
    review = reviews[0]
    assert review.status == MatchStatus.PENDING
    assert review.staging_row_id == staging.staging_id
    assert review.reason == staging.rejection_reason
    assert review.candidate_keys is None
    assert review.match_signals is None


def test_asr_app_number_conflict_opens_matching_review(db_session):
    _create_author(db_session)
    _seed_plans(db_session)

    run_import(db_session, SourceType.ASR, UPLOADED_BY, "asr1.csv", _asr_sheet(rows=1))

    conflicting = _asr_sheet(rows=1)
    conflicting.loc[0, "Campus Id"] = "654321"
    conflicting.loc[0, "Employee Id"] = "EMP002"
    conflicting.loc[0, "Cell Phone"] = "0829999999"
    conflicting.loc[0, "Email Address"] = "other@example.com"
    run_import(db_session, SourceType.ASR, UPLOADED_BY, "asr2.csv", conflicting)

    reviews = get_matching_reviews(db_session)
    assert len(reviews) == 1
    review = reviews[0]
    assert review.status == MatchStatus.PENDING
    assert "application_number 100001 already belongs to campus_id 123456" in review.reason
    assert review.candidate_keys is None
    assert review.match_signals is None


def test_asr_outdated_effective_date_opens_matching_review(db_session):
    _create_author(db_session)
    _seed_plans(db_session)

    run_import(db_session, SourceType.ASR, UPLOADED_BY, "asr1.csv", _asr_sheet(rows=1))

    outdated = _asr_sheet(rows=1)
    outdated.loc[0, "Effective Date"] = pd.Timestamp("2026-01-01")
    run_import(db_session, SourceType.ASR, UPLOADED_BY, "asr2.csv", outdated)

    reviews = get_matching_reviews(db_session)
    assert len(reviews) == 1
    review = reviews[0]
    assert review.status == MatchStatus.PENDING
    assert "outdated effective date" in review.reason
