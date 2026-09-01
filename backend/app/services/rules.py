"""Drives the rule engine for one intake.

The engine works on DataFrames rather than the ORM, so this loads the intake's
applications, marks and existing rules, hands them over, and translates what
comes back into something a router can return.
"""

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.applicant_marks import ApplicantMark
from app.models.applications import Application
from app.models.rules import Institution, Rules, RuleStatus
from app.queries import rules as rule_queries
from app.services.rule_engine import RuleEngine


class NoMarksError(Exception):
    """Raised when the intake has no marks, so no rule can be evaluated."""


def _load_frames(
    db: Session, institution: Institution, intake_year: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Pull the intake into the three frames RuleEngine expects."""
    applications = pd.DataFrame(
        db.execute(
            select(Application.campus_id, Application.application_date)
        ).mappings().all()
    )

    marks = pd.DataFrame(
        db.execute(
            select(
                ApplicantMark.campus_id,
                ApplicantMark.course_code,
                ApplicantMark.mark,
            )
        ).mappings().all()
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
            }
            for r in saved
        ],
        # named up front so an empty intake still has the columns the engine
        # filters on, instead of raising KeyError on the first rule
        columns=["rule_id", "institution", "intake_year", "status", "rule"],
    )
    return applications, marks, rules


def preview_rule(
    db: Session, institution: Institution, intake_year: int, expression: str
) -> dict:
    """Show what a proposed rule would do, without saving it."""
    applications, marks, rules = _load_frames(db, institution, intake_year)
    if marks.empty:
        raise NoMarksError(
            "No marks have been imported yet, so a rule cannot be evaluated"
        )
    engine = RuleEngine(applications, marks, rules)
    summary = engine.process_proposed_rule(institution, intake_year, expression)
    # an applicant missing a mark the rule uses is counted as not admitted, so
    # say how many that was rather than letting it quietly deflate the number
    summary["not_evaluable"] = engine.incomplete_for(expression)
    return summary


def save_rule(
    db: Session,
    institution: Institution,
    intake_year: int,
    expression: str,
    created_by: str,
) -> Rules:
    """Save a rule as the active one for this intake.

    Previewed first so a rule that cannot be evaluated is never stored, and
    because the engine is what validates the expression at all.
    """
    preview_rule(db, institution, intake_year, expression)
    return rule_queries.create_rule(
        db,
        institution=institution,
        intake_year=intake_year,
        version=rule_queries.next_version(db, institution, intake_year),
        rule=expression,
        status=RuleStatus.ACTIVE,
        created_by=created_by,
    )


def list_rules(db: Session, skip: int = 0, limit: int = 100) -> list[Rules]:
    return rule_queries.get_rules(db, skip=skip, limit=limit)
