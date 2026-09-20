"Responsible for fetching decisons data from applications and generating an excel file for the given run"

import io

import pandas as pd
from sqlalchemy.orm import Session

import app.queries.applicants as applicant_queries
import app.queries.applications as applications_queries
from app.models.applications import Application, ApplicationStatus


class NoDecisionsFoundError(Exception):
    """Rasied when no applications found for the given year"""


class MissingApplicantDataError(Exception):
    """Raised when an application being exported has no matching applicant row."""


def format_application_decision(application: Application):

    decision = ""
    status = application.application_status
    reason = application.application_status_reason

    if status == ApplicationStatus.DENIED:
        decision = f"Deny: {reason.value if reason else "no reason provided"}"

    elif status == ApplicationStatus.ACCEPTED:
        decision = "Firm Offer"

    else:
        decision = status.value

    return decision


# What "the decisions" means with no stage named: the outcomes that have been
# settled. The earlier stages are exportable too, they are just not what a
# convenor means by a decision list.
DEFAULT_EXPORT_STATUSES = [
    ApplicationStatus.ACCEPTED,
    ApplicationStatus.DENIED,
    ApplicationStatus.CONDITIONAL_OFFER,
]


def generate_decisions_by_year(
    db: Session, year: int, statuses: list[ApplicationStatus] | None = None
) -> io.BytesIO:
    """Generates a decisions excel file buffer for one intake year, for the given stages."""

    export_status_types = statuses or DEFAULT_EXPORT_STATUSES

    applications = [
        a
        for a in applications_queries.get_applications_by_intake_year(db, year)
        if a.application_status in export_status_types
    ]

    if not applications:
        named = ", ".join(s.value for s in export_status_types)
        raise NoDecisionsFoundError(
            f"No applications at stage {named} for the {year} intake. "
            f"Applications for an intake are dated the year before it starts."
        )

    campus_ids = [a.campus_id for a in applications]
    applicants = applicant_queries.get_applicants_by_campus_ids(db, campus_ids)

    applicants_by_campus_id = {a.campus_id: a for a in applicants}

    # get_applicants_by_campus_ids is an IN query, so it can legitimately come
    # back with fewer rows than applications has campus ids. .get() returning
    # None there used to raise a bare AttributeError with no indication which
    # applicant was missing. Naming every one up front, rather than failing
    # silently on the export or crashing on the first row hit, means a data
    # problem gets fixed instead of an official decisions list quietly
    # shipping with someone missing from it.
    missing_campus_ids = sorted(
        {a.campus_id for a in applications if a.campus_id not in applicants_by_campus_id}
    )
    if missing_campus_ids:
        raise MissingApplicantDataError(
            "No applicant record for campus id(s): " + ", ".join(missing_campus_ids)
        )

    decisions = pd.DataFrame(
        [
            {
                "Campus Id": a.campus_id,
                "Academic Plan": a.academic_plan1,
                "Last Name": applicants_by_campus_id[a.campus_id].last_name,
                "First Name": applicants_by_campus_id[a.campus_id].first_name,
                "Decision": format_application_decision(a),
            }
            for a in applications
        ]
    )

    buffer = io.BytesIO()
    decisions.to_excel(buffer, index=False, engine="openpyxl", sheet_name="Decisions")
    buffer.seek(0)
    return buffer
