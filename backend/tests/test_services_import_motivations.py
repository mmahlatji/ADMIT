import uuid

from app.queries.motivations import get_motivation_by_campus_id
from app.services.imports.motivations import reconcile_motivation_row
from app.services.imports.results import ReconcileOutcome
from tests.test_queries_applicants import _create as create_applicant

IMPORT_RUN_ID = uuid.uuid4()
CHANGED_BY = "9999999"


def _row(**overrides):
    row = {"campus_id": "xxxyyy001", "motivation": "I want to do honours because..."}
    row.update(overrides)
    return row


def test_created_motivation_backfills_name_from_applicant(db_session):
    create_applicant(db_session)

    outcome, campus_id, flag_reason = reconcile_motivation_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    assert outcome == ReconcileOutcome.CREATED
    assert campus_id == "xxxyyy001"
    motivation = get_motivation_by_campus_id(db_session, "xxxyyy001")
    assert motivation is not None
    # names come from the matched Applicant, not the sheet - the sheet has no name column
    assert motivation.first_name == "Noah"
    assert motivation.last_name == "Smith"
    assert motivation.motivation == "I want to do honours because..."


def test_unknown_campus_id_is_skipped(db_session):
    outcome, campus_id, flag_reason = reconcile_motivation_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    assert outcome == ReconcileOutcome.SKIPPED_UNMATCHED
    assert campus_id == "xxxyyy001"
    assert flag_reason == "no applicant found for campus_id xxxyyy001"
    assert get_motivation_by_campus_id(db_session, "xxxyyy001") is None


def test_reimport_with_blank_text_does_not_clear_existing_motivation(db_session):
    create_applicant(db_session)
    reconcile_motivation_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row())

    outcome, _, _ = reconcile_motivation_row(db_session, IMPORT_RUN_ID, CHANGED_BY, _row(motivation=None))

    # update_motivation treats motivation=None as "leave it alone", so nothing
    # actually changed even though a row for this applicant was re-imported
    assert outcome == ReconcileOutcome.UNCHANGED
    motivation = get_motivation_by_campus_id(db_session, "xxxyyy001")
    assert motivation.motivation == "I want to do honours because..."
