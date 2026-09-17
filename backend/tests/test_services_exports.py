import uuid
from datetime import date

import pandas as pd
import pytest

from app.models.applicants import CitizenshipResidency, TitleEnum
from app.models.applications import (
    Application,
    ApplicationStatus,
    Choice,
    DenyReason,
)
from app.queries.applicants import create_applicant
from app.services.exports import (
    MissingApplicantDataError,
    NoDecisionsFoundError,
    format_application_decision,
    generate_decisions_by_year,
)


def _create_applicant(
    db_session,
    campus_id="xxxyyy001",
    employee_id="1000001",
    first_name="Noah",
    last_name="Smith",
):
    return create_applicant(
        db_session,
        campus_id=campus_id,
        employee_id=employee_id,
        title=TitleEnum.MS,
        first_name=first_name,
        last_name=last_name,
        citizenship_residency=CitizenshipResidency.SA_CITIZEN,
    )


def _create_application(
    db_session,
    campus_id="xxxyyy001",
    application_number="A0000001",
    academic_plan1="BSC01",
    status=ApplicationStatus.ACCEPTED,
    reason=None,
    application_date=date(2025, 3, 1),
):
    application = Application(
        application_id=uuid.uuid4(),
        application_number=application_number,
        campus_id=campus_id,
        academic_program_code="BSC01",
        academic_plan1=academic_plan1,
        choice=Choice.FIRST,
        application_date=application_date,
        effective_date=application_date,
        application_status=status,
        application_status_reason=reason,
    )
    db_session.add(application)
    db_session.flush()
    return application


# ---------- format_application_decision ----------


def test_format_decision_denied_includes_reason(db_session):
    _create_applicant(db_session)
    application = _create_application(
        db_session, status=ApplicationStatus.DENIED, reason=DenyReason.NOT_COMPETITIVE
    )

    assert format_application_decision(application) == "Deny: Not competitive"


def test_format_decision_accepted_is_firm_offer(db_session):
    _create_applicant(db_session)
    application = _create_application(db_session, status=ApplicationStatus.ACCEPTED)

    assert format_application_decision(application) == "Firm Offer"


def test_format_decision_other_status_returns_raw_value(db_session):
    _create_applicant(db_session)
    application = _create_application(
        db_session, status=ApplicationStatus.CONDITIONAL_OFFER
    )

    assert format_application_decision(application) == "Conditional Offer"


# ---------- generate_decisions_by_year ----------


def test_generate_decisions_raises_when_none_for_year(db_session):
    with pytest.raises(NoDecisionsFoundError):
        generate_decisions_by_year(db_session, 2025)


def test_generate_decisions_raises_when_none_match_export_statuses(db_session):
    _create_applicant(db_session)
    _create_application(
        db_session, application_number="A0000001", status=ApplicationStatus.APPLIED
    )

    with pytest.raises(NoDecisionsFoundError):
        generate_decisions_by_year(db_session, 2025)


def test_generate_decisions_filters_by_year_and_status(db_session):
    _create_applicant(db_session, "xxxyyy001", "1000001", "Noah", "Smith")
    _create_applicant(db_session, "xxxyyy002", "1000002", "Amy", "Jones")

    _create_application(
        db_session,
        campus_id="xxxyyy001",
        application_number="A0000001",
        status=ApplicationStatus.ACCEPTED,
        application_date=date(2025, 2, 1),
    )
    # different year, should be excluded
    _create_application(
        db_session,
        campus_id="xxxyyy002",
        application_number="A0000002",
        status=ApplicationStatus.ACCEPTED,
        application_date=date(2024, 2, 1),
    )
    # same year, non-exportable status, should be excluded
    _create_application(
        db_session,
        campus_id="xxxyyy002",
        application_number="A0000003",
        status=ApplicationStatus.APPLIED,
        application_date=date(2025, 5, 1),
    )

    buffer = generate_decisions_by_year(db_session, 2025)

    df = pd.read_excel(buffer, engine="openpyxl")

    assert len(df) == 1
    assert df.iloc[0]["Campus Id"] == "xxxyyy001"
    assert df.iloc[0]["Last Name"] == "Smith"
    assert df.iloc[0]["Decision"] == "Firm Offer"


def test_generate_decisions_builds_expected_columns(db_session):
    _create_applicant(db_session, "xxxyyy001", "1000001", "Noah", "Smith")
    _create_application(
        db_session,
        campus_id="xxxyyy001",
        application_number="A0000001",
        academic_plan1="BSC01",
        status=ApplicationStatus.DENIED,
        reason=DenyReason.REQUIREMENTS_NOT_MET,
        application_date=date(2025, 4, 1),
    )

    buffer = generate_decisions_by_year(db_session, 2025)
    df = pd.read_excel(buffer, engine="openpyxl")

    assert list(df.columns) == [
        "Campus Id",
        "Academic Plan",
        "Last Name",
        "First Name",
        "Decision",
    ]
    row = df.iloc[0]
    assert row["Campus Id"] == "xxxyyy001"
    assert row["Academic Plan"] == "BSC01"
    assert row["Last Name"] == "Smith"
    assert row["First Name"] == "Noah"
    assert row["Decision"] == "Deny: Requirements not met"


def test_generate_decisions_names_the_missing_applicant(db_session):
    """An application with no matching applicant row used to raise a bare
    AttributeError from .get(campus_id).last_name deep inside the DataFrame
    construction. It should instead name exactly which campus id is missing
    applicant data, rather than silently drop them from an official export
    or crash with no indication of which record is broken.
    """
    # No _create_applicant call: the application exists with nothing behind it.
    _create_application(
        db_session,
        campus_id="orphan001",
        application_number="A0000001",
        status=ApplicationStatus.ACCEPTED,
        application_date=date(2025, 2, 1),
    )

    with pytest.raises(MissingApplicantDataError, match="orphan001"):
        generate_decisions_by_year(db_session, 2025)
