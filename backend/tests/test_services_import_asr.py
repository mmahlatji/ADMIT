import uuid
from datetime import date

import pytest

from app.models.academic_plans import AcademicPlanType
from app.models.applicants import CitizenshipResidency, SexEnum
from app.models.applications import ApplicationStatus, Choice, DenyReason, Semester
from app.queries.academic_plans import create_academic_plan
from app.queries.applicants import get_applicant_by_campus_id
from app.queries.applications import get_application_by_number, update_application
from app.queries.system_logs import get_system_logs
from app.services.imports.asr import (
    reconcile_asr_row,
)
from app.services.imports.results import ReconcileOutcome, RowReconciliationError
from tests.test_queries_notes import _create_author

IMPORT_RUN_ID = uuid.uuid4()
CHANGED_BY = "9999999"


def _seed_plans(db_session):
    # department "CSC" at plan_code[5:8], with one internal and one external plan
    create_academic_plan(db_session, "CSC", "SH001CSC05", AcademicPlanType.INTERNAL)
    create_academic_plan(db_session, "CSC", "SH001CSC06", AcademicPlanType.EXTERNAL)


def _row(**overrides):
    # a "clean" ASR row as reconcile_asr_row receives it: already renamed to
    # db column names by the adapter, raw sheet vocabulary still unmapped
    row = {
        "campus_id": "xxxyyy001",
        "employee_id": "1000001",
        "first_name": "Noah",
        "last_name": "Smith",
        "Title": "Mr",
        "sex": "M",
        "cell_phone": None,
        "home_phone": None,
        "email": None,
        "population_group": "African",
        "birth_date": None,
        "citizenship_residency": "SA Citizen",
        "non_sa_citizenship": None,
        "application_number": "00000001",
        "academic_program_code": "CSC",
        "academic_plan1": "SH001CSC05",
        "choice": "FRST",
        "semester": "1st Semester",
        "application_date": date(2022, 10, 1),
        "effective_date": date(2022, 10, 1),
        "last_registration": "2022:SB001:reg",
        "previous_application_term": None,
        "program_action": "APPL",
        "program_reason": "FRST",
    }
    row.update(overrides)
    return row


def test_fresh_row_creates_applicant_and_application(db_session):
    _create_author(db_session)
    _seed_plans(db_session)

    outcome, campus_id, application_number, _ = reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY, _row()
    )

    assert outcome == ReconcileOutcome.CREATED
    assert campus_id == "xxxyyy001"
    assert application_number == "00000001"

    applicant = get_applicant_by_campus_id(db_session, "xxxyyy001")
    assert applicant is not None
    assert applicant.sex == SexEnum.MALE
    assert applicant.citizenship_residency == CitizenshipResidency.SA_CITIZEN

    application = get_application_by_number(db_session, "00000001")
    assert application is not None
    assert application.choice == Choice.FIRST
    assert application.semester == Semester.FIRST
    assert application.application_status == ApplicationStatus.APPLIED
    assert application.incorrect_plan is False


def test_identical_reimport_is_a_noop(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    reconcile_asr_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())
    logs_after_first_import = len(get_system_logs(db_session))

    outcome, _, _, _ = reconcile_asr_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    assert outcome == ReconcileOutcome.UNCHANGED
    assert len(get_system_logs(db_session)) == logs_after_first_import


def test_changed_field_updates_in_place_with_one_audit_entry(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    reconcile_asr_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    outcome, _, _, _ = reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY, _row(academic_program_code="MAM")
    )

    assert outcome == ReconcileOutcome.UPDATED
    application = get_application_by_number(db_session, "00000001")
    assert application.academic_program_code == "MAM"

    application_logs = [log for log in get_system_logs(db_session) if log.entity_name == "applications"]
    assert len(application_logs) == 2
    # Matched rather than indexed: both entries are written inside one
    # transaction, and changed_at is a transaction-start timestamp, so they tie
    # on the sort key and neither end of the list is reliably the later one.
    updates = [log for log in application_logs if log.new_data == {"academic_program_code": "MAM"}]
    assert len(updates) == 1


def test_application_number_pointing_at_different_campus_id_is_skipped(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    reconcile_asr_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    outcome, campus_id, application_number, flag_reason = reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(campus_id="xxxyyy002", employee_id="1000002"),
    )

    assert outcome == ReconcileOutcome.SKIPPED_UNMATCHED
    assert campus_id == "xxxyyy002"
    assert application_number == "00000001"
    assert flag_reason == "application_number 00000001 already belongs to campus_id xxxyyy001"
    application = get_application_by_number(db_session, "00000001")
    assert application.campus_id == "xxxyyy001"


def test_missing_action_reason_defaults_to_applied(db_session):
    _create_author(db_session)
    _seed_plans(db_session)

    outcome, _, _, _ = reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(program_action=None, program_reason=None),
    )

    assert outcome == ReconcileOutcome.CREATED
    application = get_application_by_number(db_session, "00000001")
    assert application.application_status == ApplicationStatus.APPLIED


def test_unrecognized_action_reason_rejected_on_create(db_session):
    _create_author(db_session)
    _seed_plans(db_session)

    with pytest.raises(RowReconciliationError):
        reconcile_asr_row(
            db_session, IMPORT_RUN_ID, CHANGED_BY,
            _row(program_action="ZZZZ", program_reason="XXXX"),
        )


def test_unknown_department_is_rejected(db_session):
    _create_author(db_session)
    _seed_plans(db_session)

    with pytest.raises(RowReconciliationError):
        reconcile_asr_row(
            db_session, IMPORT_RUN_ID, CHANGED_BY,
            _row(academic_plan1="SH001MAM05"),
        )


def test_transition_advances_status(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    reconcile_asr_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    outcome, _, _, _ = reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(program_action="DDEF", program_reason="HCOF"),
    )

    assert outcome == ReconcileOutcome.UPDATED
    application = get_application_by_number(db_session, "00000001")
    assert application.application_status == ApplicationStatus.REVIEWED


def test_unrecognized_transition_flags_row_on_update(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    reconcile_asr_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    outcome, campus_id, application_number, flag_reason = reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(program_action="ZZZZ", program_reason="XXXX"),
    )

    assert outcome == ReconcileOutcome.SKIPPED_UNMATCHED
    assert campus_id == "xxxyyy001"
    assert application_number == "00000001"
    assert "unrecognized program action/reason" in flag_reason


def test_outdated_effective_date_flags_row(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    reconcile_asr_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    outcome, campus_id, application_number, flag_reason = reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(effective_date=date(2022, 9, 1)),
    )

    assert outcome == ReconcileOutcome.SKIPPED_UNMATCHED
    assert campus_id == "xxxyyy001"
    assert application_number == "00000001"
    assert "outdated effective date" in flag_reason


def test_outdated_effective_date_and_unrecognized_transition_accumulate(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    reconcile_asr_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    outcome, _, _, flag_reason = reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(effective_date=date(2022, 9, 1), program_action="ZZZZ", program_reason="XXXX"),
    )

    assert outcome == ReconcileOutcome.SKIPPED_UNMATCHED
    assert "outdated effective date" in flag_reason
    assert "unrecognized program action/reason" in flag_reason
    assert "; " in flag_reason


def test_newer_effective_date_updates(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    reconcile_asr_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    outcome, _, _, _ = reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(effective_date=date(2022, 11, 1)),
    )

    assert outcome == ReconcileOutcome.UPDATED
    application = get_application_by_number(db_session, "00000001")
    assert application.effective_date == date(2022, 11, 1)


def test_uct_student_on_external_plan_flagged_incorrect(db_session):
    _create_author(db_session)
    _seed_plans(db_session)

    reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(academic_plan1="SH001CSC06", last_registration="2022:SB001:reg"),
    )

    application = get_application_by_number(db_session, "00000001")
    assert application.incorrect_plan is True
    assert application.requires_plan_correction is True


def test_dates_parsed_from_iso_strings(db_session):
    _create_author(db_session)
    _seed_plans(db_session)

    reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(application_date="2022-10-01", effective_date="2022-10-01"),
    )

    application = get_application_by_number(db_session, "00000001")
    assert application.application_date == date(2022, 10, 1)
    assert application.effective_date == date(2022, 10, 1)


def test_missing_dates_on_create_is_rejected(db_session):
    _create_author(db_session)
    _seed_plans(db_session)

    with pytest.raises(RowReconciliationError):
        reconcile_asr_row(
            db_session, IMPORT_RUN_ID, CHANGED_BY,
            _row(application_date=None, effective_date=None),
        )


def test_duplicate_application_is_denied(db_session):
    _create_author(db_session)
    _seed_plans(db_session)

    # UCT student on the external plan -> incorrect
    reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(application_number="00000001", academic_plan1="SH001CSC06", last_registration="2022:SB001:reg"),
    )
    # same student also on the internal plan -> correct
    reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(application_number="00000002", academic_plan1="SH001CSC05", last_registration="2022:SB001:reg"),
    )

    incorrect = get_application_by_number(db_session, "00000001")
    assert incorrect.application_status == ApplicationStatus.DENIED
    assert incorrect.duplicate_application is True
    assert incorrect.application_status_reason == DenyReason.DUPLICATE_APPLICATION
    assert incorrect.requires_plan_correction is False

    correct = get_application_by_number(db_session, "00000002")
    assert correct.application_status == ApplicationStatus.APPLIED
    assert correct.duplicate_application is False


def _seed_duplicate_pair(db_session):
    """Two applications for one student in the same department, the first on the
    wrong plan so duplicate detection picks it out.
    """
    reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(application_number="00000001", academic_plan1="SH001CSC06", last_registration="2022:SB001:reg"),
    )
    reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(application_number="00000002", academic_plan1="SH001CSC05", last_registration="2022:SB001:reg"),
    )


def test_reimport_does_not_reverse_a_convenor_decision(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    _seed_duplicate_pair(db_session)

    # a convenor overrules the auto-denial: this is the application to keep
    overruled = get_application_by_number(db_session, "00000001")
    update_application(db_session, overruled, application_status=ApplicationStatus.ACCEPTED)

    # a later routine import of the other row re-runs duplicate detection
    outcome, _, _, flag_reason = reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(application_number="00000002", academic_plan1="SH001CSC05", last_registration="2022:SB001:reg"),
    )

    assert outcome == ReconcileOutcome.SKIPPED_UNMATCHED
    assert "already Accepted" in flag_reason

    kept = get_application_by_number(db_session, "00000001")
    assert kept.application_status == ApplicationStatus.ACCEPTED


def test_cleared_plan_correction_survives_reimport(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    # starts on the correct (internal) plan, so no correction needed
    reconcile_asr_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    # the sheet now shows a UCT student on the external plan: a new mismatch,
    # so the import raises the work item
    wrong_plan = _row(academic_plan1="SH001CSC06", last_registration="2022:SB001:reg")
    reconcile_asr_row(db_session, IMPORT_RUN_ID, CHANGED_BY, wrong_plan)

    application = get_application_by_number(db_session, "00000001")
    assert application.incorrect_plan is True
    assert application.requires_plan_correction is True

    # a convenor sorts the plan out and closes the work item
    update_application(db_session, application, requires_plan_correction=False)

    # the next import still sees the stale mismatch in the sheet
    reconcile_asr_row(db_session, IMPORT_RUN_ID, CHANGED_BY, wrong_plan)

    application = get_application_by_number(db_session, "00000001")
    # incorrect_plan is an observation, so it stays true while the sheet says so
    assert application.incorrect_plan is True
    # but the work item a human closed stays closed
    assert application.requires_plan_correction is False


def test_three_applications_are_flagged_not_crashed(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    create_academic_plan(db_session, "MAM", "SH001MAM05", AcademicPlanType.INTERNAL)
    _seed_duplicate_pair(db_session)

    # a third live application in the same cycle, in a different department:
    # determine_duplicate can't judge this, so it must flag rather than blow up
    outcome, _, _, flag_reason = reconcile_asr_row(
        db_session, IMPORT_RUN_ID, CHANGED_BY,
        _row(application_number="00000003", academic_plan1="SH001MAM05", last_registration="2022:SB001:reg"),
    )

    assert outcome == ReconcileOutcome.SKIPPED_UNMATCHED
    assert "too many to pick a duplicate automatically" in flag_reason


def test_duplicate_still_denied_when_nobody_has_decided(db_session):
    _create_author(db_session)
    _seed_plans(db_session)
    _seed_duplicate_pair(db_session)

    # guard must not block the normal case: still APPLIED means still auto-deniable
    denied = get_application_by_number(db_session, "00000001")
    assert denied.application_status == ApplicationStatus.DENIED





