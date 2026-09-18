"""Drives the rule engine for one intake.

The engine works on DataFrames rather than the ORM, so this loads the intake's
applications, marks and existing rules, hands them over, and translates what
comes back into something a router can return.
"""

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.applicant_marks import ApplicantMark
from app.models.applications import Application, ApplicationStatus, DenyReason
from app.models.rules import Institution, RuleAction, Rules, RuleStatus
from app.queries import applicant_marks as mark_queries
from app.queries import applications as application_queries
from app.queries import rules as rule_queries
from app.services.applications import transition_status
from app.services.engine.tools import SYSTEM_ACTOR
from app.services.rule_engine import RuleEngine


class NoMarksError(Exception):
    """Raised when the intake has no marks, so no rule can be evaluated."""


class NoRuleException(Exception):
    """Raised when a rule has not been added for an institution"""


class NoApplicationsException(Exception):
    """Raised when the intake has no applications (rare)"""


def _load_frames(
    db: Session, institution: Institution, intake_year: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Pull the intake into the three frames RuleEngine expects."""
    applications = pd.DataFrame(
        db.execute(select(Application.campus_id, Application.application_date))
        .mappings()
        .all()
    )

    marks = pd.DataFrame(
        db.execute(
            select(
                ApplicantMark.campus_id,
                ApplicantMark.course_code,
                ApplicantMark.mark,
            )
        )
        .mappings()
        .all()
    )

    saved = rule_queries.get_rules_for_intake(db, institution, intake_year)
    rules = pd.DataFrame(
        [
            {
                "rule_id": str(r.rule_id),
                "institution": r.institution,
                "intake_year": r.intake_year,
                "status": r.status,
                "rule": r.rule,
                "rule_action": r.rule_action,
            }
            for r in saved
        ],
        # named up front so an empty intake still has the columns the engine
        # filters on, instead of raising KeyError on the first rule
        columns=[
            "rule_id",
            "institution",
            "intake_year",
            "status",
            "rule",
            "rule_action",
        ],
    )
    return applications, marks, rules


def preview_rule(
    db: Session,
    institution: Institution,
    intake_year: int,
    expression: str,
    action: RuleAction,
) -> dict:
    """Show what a proposed rule would do, without saving it."""
    applications, marks, rules = _load_frames(db, institution, intake_year)
    if marks.empty:
        raise NoMarksError(
            "No marks have been imported yet, so a rule cannot be evaluated"
        )
    engine = RuleEngine(applications, marks, rules)
    summary = engine.process_proposed_rule(institution, intake_year, expression, action)
    # an applicant missing a mark the rule uses is counted as not admitted, so
    # say how many that was rather than letting it quietly deflate the number
    summary["not_evaluable"] = engine.incomplete_for(expression)
    return summary


def save_rule(
    db: Session,
    institution: Institution,
    intake_year: int,
    expression: str,
    rule_action: RuleAction,
    created_by: str,
) -> Rules:
    """Save a rule as the active one for this intake.

    Previewed first so a rule that cannot be evaluated is never stored, and
    because the engine is what validates the expression at all.
    """
    preview_rule(db, institution, intake_year, expression, rule_action)
    return rule_queries.create_rule(
        db,
        institution=institution,
        intake_year=intake_year,
        version=rule_queries.next_version(db, institution, intake_year),
        rule=expression,
        status=RuleStatus.ACTIVE,
        action=rule_action,
        created_by=created_by,
    )


def list_rules(db: Session, skip: int = 0, limit: int = 100) -> list[Rules]:
    return rule_queries.get_rules(db, skip=skip, limit=limit)


def rules_to_df(rules: list[Rules]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "rule_id": r.rule_id,
                "institution": r.institution,
                "intake_year": r.intake_year,
                "status": r.status,
                "rule": r.rule,
                "rule_action": r.rule_action,
            }
            for r in rules
        ]
    )



def _institution_for(last_registration) -> Institution:
    """Classify one applicant by whether they hold a UCT registration.

    Three shapes of "no registration" all have to land on OTHER. NaN reaches
    this from pandas and has no .strip(), which used to raise. None is what the
    ORM gives for a null column. Blank and whitespace-only strings are what the
    ASR sheet actually contains: in the October 2022 sheet, 226 of 345 rows
    carry a single space and not one is null, so treating any non-null value as
    a registration reclassifies most of the intake as UCT and judges them by the
    wrong rules.
    """
    if last_registration is None or pd.isna(last_registration):
        return Institution.OTHER
    return Institution.UCT if str(last_registration).strip() else Institution.OTHER


def apply_rules(db: Session, intake_year: int):
    """Actually updates the admission status of applicants using the current existing rule"""

    rules_by_institution = {
        institution: rule_queries.get_active_rules(db, institution, intake_year)
        for institution in Institution
    }

    if not any(rules_by_institution.values()):
        raise NoRuleException(f"No current active rules for {intake_year}")

    apps = application_queries.get_applications_by_status_and_year(
        db,
        statuses=[
            ApplicationStatus.REVIEWED,
            ApplicationStatus.CONDITIONAL_OFFER,
            ApplicationStatus.APPLIED,
        ],
        intake_year=intake_year,
    )

    if not apps:
        raise NoApplicationsException(f"No applications exist for {intake_year}")

    apps_by_campus_id = {a.campus_id: a for a in apps}

    marks = pd.DataFrame(
        [
            {"campus_id": m.campus_id, "course_code": m.course_code, "mark": m.mark}
            for m in mark_queries.get_applicant_marks_by_ids(
                db, apps_by_campus_id.keys()
            )
        ],
        # Named up front like the rules frame above: if nobody has marks
        # imported yet, the query returns nothing and this would otherwise
        # be a DataFrame with no columns at all, so the .isin() filter below
        # raises KeyError on campus_id before a single institution is tried.
        columns=["campus_id", "course_code", "mark"],
    )

    # UCT applicants carry a UCT registration on file; everyone else is from
    # another university, so classify by last_registration rather than guessing
    # from the academic plan code.
    apps_df = pd.DataFrame(
        [
            {"campus_id": a.campus_id, "last_registration": a.last_registration}
            for a in apps
        ]
    )

    apps_df["institution"] = apps_df["last_registration"].apply(_institution_for)

    for institution, rules in rules_by_institution.items():

        if not rules:
            continue

        inst_apps = apps_df[apps_df["institution"] == institution]
        inst_marks = marks[marks["campus_id"].isin(inst_apps["campus_id"])]
        rule_df = rules_to_df(rules)

        engine = RuleEngine(inst_apps, inst_marks, rule_df)
        decisions = engine.apply_all_rules(rule_df)

        for _, row in decisions.iterrows():
            application = apps_by_campus_id.get(row["campus_id"])
            if application is None:  # shouldnt happen
                continue

            if row["accepted"] and row["rejected"]:
                # An accept rule and a reject rule both fired for the same
                # applicant. The conflict check only runs when a rule is first
                # proposed, so it cannot see this if the colliding rule already
                # existed. Leaving the application where it is means a person
                # is not silently pushed either way by an outcome nobody
                # actually decided.
                continue

            if row["accepted"]:
                transition_status(
                    db, SYSTEM_ACTOR, application, ApplicationStatus.ACCEPTED
                )

            elif row["rejected"]:
                transition_status(
                    db,
                    SYSTEM_ACTOR,
                    application,
                    ApplicationStatus.DENIED,
                    DenyReason.REQUIREMENTS_NOT_MET,
                )
            elif (
                application.application_status == ApplicationStatus.APPLIED
                and row["pending"]
            ):
                transition_status(
                    db, SYSTEM_ACTOR, application, ApplicationStatus.REVIEWED
                )
