"""save_rule has to retire the version it replaces, or the engine ORs both."""

from unittest.mock import patch

from app.models.rules import Institution, RuleAction, RuleStatus
from app.queries.rules import create_rule, get_active_rules
from app.services.rules import save_rule
from tests.test_queries_notes import _create_author

INTAKE_YEAR = 2026


def _existing(db_session, action, expression, version):
    return create_rule(
        db_session,
        institution=Institution.UCT,
        intake_year=INTAKE_YEAR,
        version=version,
        rule=expression,
        status=RuleStatus.ACTIVE,
        action=action,
        created_by="9999999",
    )


@patch("app.services.rules.preview_rule")
def test_saving_leaves_the_opposite_action_active(_preview, db_session):
    _create_author(db_session)
    _existing(db_session, RuleAction.REJECT, "csc3003s <= 40", 1)

    save_rule(
        db_session,
        Institution.UCT,
        INTAKE_YEAR,
        "csc3003s >= 70",
        RuleAction.ACCEPT,
        "9999999",
    )

    active = get_active_rules(db_session, Institution.UCT, INTAKE_YEAR)
    assert {(r.rule, r.rule_action) for r in active} == {
        ("csc3003s <= 40", RuleAction.REJECT),
        ("csc3003s >= 70", RuleAction.ACCEPT),
    }
