import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rules import Institution, RuleAction, Rules, RuleStatus


def get_rule_by_id(db: Session, rule_id: uuid.UUID) -> Rules | None:
    """Look up a rule by its id. Returns None if it doesn't exist yet."""
    return db.execute(select(Rules).where(Rules.rule_id == rule_id)).scalar_one_or_none()


def get_rules(db: Session, skip: int = 0, limit: int = 100) -> list[Rules]:
    """List rules, newest first, paginated."""
    return list(
        db.execute(
            select(Rules).order_by(Rules.created_at.desc()).offset(skip).limit(limit)
        ).scalars()
    )


def get_rules_for_intake(
    db: Session, institution: Institution, intake_year: int
) -> list[Rules]:
    """Every rule ever written for one institution's intake, any status."""
    return list(
        db.execute(
            select(Rules)
            .where(Rules.institution == institution, Rules.intake_year == intake_year)
            .order_by(Rules.version.asc())
        ).scalars()
    )


def get_active_rules(
    db: Session, institution: Institution, intake_year: int
) -> list[Rules]:
    """The rules currently deciding admission for one intake."""
    return list(
        db.execute(
            select(Rules)
            .where(
                Rules.institution == institution,
                Rules.intake_year == intake_year,
                Rules.status == RuleStatus.ACTIVE,
            )
            .order_by(Rules.version.asc())
        ).scalars()
    )


def next_version(db: Session, institution: Institution, intake_year: int) -> int:
    """Next free version number for an intake.

    (institution, intake_year, version) is unique, so this has to be derived
    rather than guessed by the caller.
    """
    existing = db.execute(
        select(Rules.version).where(
            Rules.institution == institution, Rules.intake_year == intake_year
        )
    ).scalars()
    return max(existing, default=0) + 1


def create_rule(
    db: Session,
    institution: Institution,
    intake_year: int,
    version: int,
    rule: str,
    status: RuleStatus,
    action: RuleAction,
    created_by: str,
) -> Rules:
    """Insert a new rule row."""
    row = Rules(
        rule_id=uuid.uuid4(),
        institution=institution,
        intake_year=intake_year,
        version=version,
        rule=rule,
        status=status,
        rule_action=action,
        created_by=created_by,
    )
    db.add(row)
    db.flush()
    return row


def update_rule(
    db: Session,
    rule: Rules,
    institution: Institution | None = None,
    intake_year: int | None = None,
    version: int | None = None,
    expression: str | None = None,
    status: RuleStatus | None = None,
    action: RuleAction | None = None,
) -> Rules:
    """Partially update a rule, only sets fields explicitly passed."""
    fields = {
        "institution": institution,
        "intake_year": intake_year,
        "version": version,
        "rule": expression,
        "status": status,
        "rule_action": action
    }
    for field, value in fields.items():
        if value is not None:
            setattr(rule, field, value)
    db.flush()
    return rule


def delete_rule(db: Session, rule: Rules) -> None:
    """Delete a rule row."""
    db.delete(rule)
    db.flush()
