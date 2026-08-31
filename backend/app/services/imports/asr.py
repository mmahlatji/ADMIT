"""Reconciles one normalized ASR row into an Applicant and an Application.

One ASR row carries fields for both entities at once (see ASR_OUTPUT_COLUMNS
in app/adapters/columns/asr.py), so this is the one reconciler that has to
split a row and upsert two things.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.applicants import TitleEnum
from app.models.applications import ApplicationStatus, DenyReason, Semester
from app.queries.applicants import (
    create_applicant,
    update_applicant,
)
from app.queries.applications import (
    create_application,
    update_application,
)
from app.services.imports import lookups
from app.services.imports.audit import record_change
from app.services.imports.results import (
    ReconcileOutcome,
    RowReconciliationError,
    combine_outcomes,
)
from app.services.imports.value_mapping import (
    CHOICE_MAP,
    CITIZENSHIP_MAP,
    SEMESTER_MAP,
    SEX_MAP,
    TITLE_MAP,
    coerce,
    parse_date,
    parse_int,
)
from app.services.state.application_state_machine import (
    get_candidate_transition_state,
    infer_initial_state,
)
from app.services.state.application_state_service import (
    compute_incorrect_and_requires_plan_change_flags,
    determine_duplicate,
    get_action_reason,
    resolve_plans,
)

# What the before/after audit snapshots cover, diffed into a SystemLog entry.
# NOT a write allow-list: the applicant_fields/application_fields dicts built
# per row below are what actually get written. The decision fields sit here on
# purpose so status changes get audited. The import does write some of them now
# (incorrect_plan recomputed each run, application_status driven by the state
# machine); what stops that trampling a person's call is the APPLIED guard on
# the denial path below, plus requires_plan_correction being raise-only.
# Votes and notes stay out of the importer's reach entirely.
_APPLICANT_FIELDS = (
    "employee_id",
    "first_name",
    "last_name",
    "title",
    "sex",
    "cell_phone",
    "home_phone",
    "email",
    "population_group",
    "birth_date",
    "citizenship_residency",
    "non_sa_citizenship",
)
_APPLICATION_FIELDS = (
    "academic_program_code",
    "academic_plan1",
    "choice",
    "semester",
    "application_date",
    "effective_date",
    "last_registration",
    "previous_application_term",
    "application_status",
    "incorrect_plan",
    "duplicate_application",
    "application_status_reason",
    "requires_plan_correction",
)
# fields that will allow detection of duplicates and or incorrect applications
_DUPLICATE_FIELDS = (
    "requires_plan_correction",
    "duplicate_application",
    "application_status",
    "application_status_reason",
)


def _snapshot(obj, fields: tuple[str, ...]) -> dict:
    """Read the current value of each import-owned field, for before/after diffing."""
    return {field: getattr(obj, field) for field in fields}


def reconcile_asr_row(
    db: Session, import_run_id: uuid.UUID, changed_by: str, row: dict
) -> tuple[ReconcileOutcome, str, str, str | None]:
    """Upsert the Applicant and Application implied by one ASR row.

    Returns (combined_outcome, matched_campus_id, matched_application_id,
    flag_reason) for the orchestrator to stage and count; flag_reason is None
    unless the row was skipped for manual matching.
    """
    campus_id = row["campus_id"]
    row["application_number"] = str(row["application_number"])
    row["employee_id"] = str(row["employee_id"])
    # campus_id/employee_id/first_name/last_name/citizenship_residency are all
    # critical (NON_NULL) columns on the ASR adapter, so a "clean" row is
    # guaranteed to have them - safe to index directly rather than .get()
    applicant_fields = {
        "employee_id": str(row["employee_id"]),
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "title": coerce(row.get("title"), TITLE_MAP, "title"),
        "sex": coerce(row.get("sex"), SEX_MAP, "sex"),
        "cell_phone": row.get("cell_phone"),
        "home_phone": row.get("home_phone"),
        "email": row.get("email"),
        "population_group": row.get("population_group"),
        "birth_date": row.get("birth_date"),
        "citizenship_residency": coerce(
            row["citizenship_residency"], CITIZENSHIP_MAP, "citizenship_residency"
        ),
        "non_sa_citizenship": row.get("non_sa_citizenship"),
    }
    applicant_fields["title"] = applicant_fields["title"] or TitleEnum.UNSPECIFIED

    applicant = lookups.applicant_by_campus_id(db, campus_id)
    if applicant is None:
        applicant = create_applicant(db, campus_id=campus_id, **applicant_fields)
        # so later rows for the same student in this sheet find them
        lookups.remember_applicant(db, applicant)
        record_change(
            db,
            "applicants",
            applicant.applicant_id,
            changed_by,
            import_run_id,
            {},
            applicant_fields,
        )
        applicant_outcome = ReconcileOutcome.CREATED
    else:
        before = _snapshot(applicant, _APPLICANT_FIELDS)
        update_applicant(db, applicant, **applicant_fields)
        after = _snapshot(applicant, _APPLICANT_FIELDS)
        record_change(
            db,
            "applicants",
            applicant.applicant_id,
            changed_by,
            import_run_id,
            before,
            after,
        )
        applicant_outcome = (
            ReconcileOutcome.UPDATED if before != after else ReconcileOutcome.UNCHANGED
        )

    # Applicant lifecycle management, incorrect flagging and duplicate detection
    application_number = row["application_number"]
    action_reason = get_action_reason(row)
    plans = resolve_plans(db, row["academic_plan1"])

    if plans is None:
        department = row["academic_plan1"][5:8]
        raise RowReconciliationError(f"Unknown department: {department}")
    internal_plan, external_plan = plans

    last_reg = (
        row.get("last_registration") if row.get("last_registration") is not None else ""
    )
    incorrect_plan, requires_plan_correction = (
        compute_incorrect_and_requires_plan_change_flags(
            row["academic_plan1"], last_reg, internal_plan, external_plan
        )
    )

    application_date = parse_date(row.get("application_date"))
    effective_date = parse_date(row.get("effective_date"))

    application_fields = {
        "academic_program_code": row["academic_program_code"],
        "academic_plan1": row["academic_plan1"],
        "choice": coerce(row["choice"], CHOICE_MAP, "choice"),
        "semester": coerce(row.get("semester"), SEMESTER_MAP, "semester"),
        "application_date": application_date,
        "effective_date": effective_date,
        "last_registration": row.get("last_registration"),
        "previous_application_term": parse_int(row.get("previous_application_term")),
        "incorrect_plan": incorrect_plan,
        "requires_plan_correction": requires_plan_correction,
    }
    application_fields["semester"] = (
        application_fields["semester"] or Semester.UNSPECIFIED
    )

    application = lookups.application_by_number(db, application_number)
    application_errors: list[str] = []
    if application is None:
        # application_date/effective_date are NOT NULL on Application but aren't
        # critical (NON_NULL) columns on the adapter, so a clean row could still
        # be missing them - flag it now with a clear reason instead of crashing
        # on an IntegrityError deep inside create_application
        if application_date is None or effective_date is None:
            raise RowReconciliationError(
                f"application {application_number} is missing application_date/effective_date, "
                "required to create a new application"
            )
        status = ApplicationStatus.APPLIED
        if action_reason is not None:
            status = infer_initial_state(*action_reason)
            if status is None:
                raise RowReconciliationError(
                    f"Application {application_number} has an unrecognized program action/reason {action_reason!r}, application state cannot be defined."
                )

        application = create_application(
            db,
            application_number=application_number,
            campus_id=campus_id,
            application_status=status,
            **application_fields,
        )
        lookups.remember_application(db, application)

        application_fields["application_status"] = status
        record_change(
            db,
            "applications",
            application.application_id,
            changed_by,
            import_run_id,
            {},
            application_fields,
        )
        application_outcome = ReconcileOutcome.CREATED
    elif application.campus_id != campus_id:
        # this application number is now claimed by a different applicant than
        # before - never silently reassign the FK, flag it for a human instead.
        # (the applicant upsert above still went ahead - their bio data is fine
        # on its own, it's specifically this application's ownership that's in doubt)
        return (
            ReconcileOutcome.SKIPPED_UNMATCHED,
            campus_id,
            application_number,
            f"application_number {application_number} already belongs to campus_id {application.campus_id}",
        )
    else:
        before = _snapshot(application, _APPLICATION_FIELDS)
        updated_application = dict(application_fields)

        # requires_plan_correction is workflow state a human owns, unlike
        # incorrect_plan which is a pure observation recomputed every run. The
        # import may RAISE it when a mismatch first appears, but never lowers
        # it, so a convenor clearing the work item stays cleared even though the
        # sheet keeps reporting the same mismatch until the export catches up.
        if incorrect_plan and not application.incorrect_plan:
            updated_application["requires_plan_correction"] = True
        else:
            updated_application["requires_plan_correction"] = None  # leave it alone

        # checking of the effective date incase data is stale
        if (
            effective_date is not None
            and application.effective_date is not None
            and effective_date < application.effective_date
        ):
            application_errors.append(
                f"outdated effective date {effective_date}: earlier than current {application.effective_date}"
            )
        elif effective_date is None or (effective_date == application.effective_date):
            updated_application["effective_date"] = (
                None  # Dont change it when update is called
            )

        if action_reason is not None:
            transition = get_candidate_transition_state(
                application.application_status, *action_reason
            )
            if transition is None:
                application_errors.append(
                    f"unrecognized program action/reason {action_reason!r} i.e invalid transition"
                )
            elif transition != application.application_status:
                updated_application["application_status"] = transition

        if not application_errors:
            update_application(db, application, **updated_application)
            after = _snapshot(application, _APPLICATION_FIELDS)
            record_change(
                db,
                "applications",
                application.application_id,
                changed_by,
                import_run_id,
                before,
                after,
            )
            application_outcome = (
                ReconcileOutcome.UPDATED
                if before != after
                else ReconcileOutcome.UNCHANGED
            )

    if application_errors:
        return (
            ReconcileOutcome.SKIPPED_UNMATCHED,
            campus_id,
            application_number,
            "; ".join(application_errors),
        )

    # Duplicate detection and denial
    applications = lookups.active_applications_for(db, campus_id, application.application_date)

    # this query isn't department-scoped, so a student applying to three
    # departments lands here with three rows. determine_duplicate can only judge
    # an unambiguous pair, so anything more goes to a human rather than being
    # guessed at (it also used to crash here on a two-way unpack).
    if len(applications) > 2:
        return (
            ReconcileOutcome.SKIPPED_UNMATCHED,
            campus_id,
            application_number,
            (
                f"{len(applications)} live applications for campus_id {campus_id} this cycle, "
                "too many to pick a duplicate automatically"
            ),
        )

    duplicate = determine_duplicate(applications)

    if duplicate is None:
        return combine_outcomes(applicant_outcome, application_outcome), campus_id, application_number, None

    # a convenor's decision outranks the importer: only auto-deny an application
    # nobody has ruled on yet. Past APPLIED means someone (or the sheet's own
    # lifecycle) already formed a view, and a routine re-import must not silently
    # reverse it. Flagged for review instead so the duplicate isn't just dropped.
    if duplicate.application_status is not ApplicationStatus.APPLIED:
        return (
            ReconcileOutcome.SKIPPED_UNMATCHED,
            campus_id,
            application_number,
            (
                f"application {duplicate.application_number} looks like a duplicate but is "
                f"already {duplicate.application_status.value}, leaving the existing decision alone"
            ),
        )

    before = _snapshot(duplicate, _DUPLICATE_FIELDS)
    update_application(
        db,
        duplicate,
        requires_plan_correction=False,
        duplicate_application=True,
        application_status=ApplicationStatus.DENIED,
        application_status_reason=DenyReason.DUPLICATE_APPLICATION,
    )
    after = _snapshot(duplicate, _DUPLICATE_FIELDS)
    record_change(
        db,
        "applications",
        duplicate.application_id,
        changed_by,
        import_run_id,
        before,
        after,
    )
    return (
        combine_outcomes(applicant_outcome, application_outcome),
        campus_id,
        application_number,
        None,
    )
