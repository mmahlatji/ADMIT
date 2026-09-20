"""A preview describes one institution's slice of one intake.

RuleEngine counts the rows in the marks frame and never reads the
applications one, so narrowing only the applications left every preview
reporting on every applicant with marks in the database, whatever intake or
institution was asked for.

Deliberately not narrowed by status: a preview answers what a rule would do
to the cohort, not what pressing Apply would change right now.
"""

from datetime import date

import pytest

from app.models.applicant_marks import ResultCode
from app.models.applications import ApplicationStatus, Choice
from app.models.rules import Institution, RuleAction
from app.queries.applicant_marks import create_applicant_mark
from app.queries.applicants import create_applicant
from app.queries.applications import create_application
from app.services.rules import NoMarksError, preview_rule

EXPRESSION = "csc3003s >= 50"


def _applicant_with_mark(
    db_session, campus_id, mark, *, last_registration, when, status
):
    create_applicant(
        db_session,
        campus_id=campus_id,
        employee_id=campus_id[-7:].rjust(7, "0"),
        title="Mr",
        first_name="Test",
        last_name="Person",
        citizenship_residency="SA Citizen",
    )
    create_application(
        db_session,
        application_number=campus_id[:8],
        campus_id=campus_id,
        academic_program_code="CSC",
        academic_plan1="CSC05",
        choice=Choice.FIRST,
        application_status=status,
        application_date=when,
        effective_date=when,
        last_registration=last_registration,
    )
    create_applicant_mark(db_session, campus_id, "CSC3003S", mark, ResultCode.NONE)


def test_preview_counts_only_the_requested_institution(db_session):
    _applicant_with_mark(
        db_session,
        "uctaaa001",
        80,
        last_registration="2022",
        when=date(2022, 5, 1),
        status=ApplicationStatus.APPLIED,
    )
    _applicant_with_mark(
        db_session,
        "othaaa001",
        80,
        last_registration=" ",
        when=date(2022, 5, 1),
        status=ApplicationStatus.APPLIED,
    )

    uct = preview_rule(db_session, Institution.UCT, 2023, EXPRESSION, RuleAction.ACCEPT)

    assert uct["after"] == 1
    assert uct["pass_rate_after"] == 100.0


def test_preview_counts_only_the_requested_intake(db_session):
    _applicant_with_mark(
        db_session,
        "uctaaa001",
        80,
        last_registration="2022",
        when=date(2022, 5, 1),
        status=ApplicationStatus.APPLIED,
    )

    # the 2024 intake is applied for during 2023, so this applicant is not in it
    with pytest.raises(NoMarksError):
        preview_rule(db_session, Institution.UCT, 2024, EXPRESSION, RuleAction.ACCEPT)


def test_preview_still_counts_applicants_already_decided(db_session):
    """The cohort question, not the "what would Apply change" question. Most
    of a finished intake is decided, and leaving those out made the headline
    number look like the rule barely applied to anyone."""
    _applicant_with_mark(
        db_session,
        "uctaaa001",
        80,
        last_registration="2022",
        when=date(2022, 5, 1),
        status=ApplicationStatus.APPLIED,
    )
    _applicant_with_mark(
        db_session,
        "uctbbb002",
        80,
        last_registration="2022",
        when=date(2022, 5, 1),
        status=ApplicationStatus.DENIED,
    )

    result = preview_rule(
        db_session, Institution.UCT, 2023, EXPRESSION, RuleAction.ACCEPT
    )

    assert result["after"] == 2
