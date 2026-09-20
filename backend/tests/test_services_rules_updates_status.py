"""update_rule_status looks the rule up before delegating the update."""

import pytest

from app.models.rules import Institution, RuleAction, RuleStatus
from app.queries.rules import create_rule
from app.services.rules import (
    NoRuleException,
    InvalidRuleTransitionError,
    update_rule_status,
)
from tests.test_queries_notes import _create_author
import uuid

INTAKE_YEAR = 2026


def _existing(db_session, status, version=1):
    return create_rule(
        db_session,
        institution=Institution.UCT,
        intake_year=INTAKE_YEAR,
        version=version,
        rule="csc3003s >= 60",
        status=status,
        action=RuleAction.ACCEPT,
        created_by="9999999",
    )


def test_update_rule_status_flips_an_existing_rule(db_session):
    _create_author(db_session)
    rule = _existing(db_session, RuleStatus.ACTIVE)

    updated = update_rule_status(db_session, rule.rule_id, RuleStatus.INACTIVE)

    assert updated.status is RuleStatus.INACTIVE
    assert updated.rule_id == rule.rule_id


def test_update_rule_status_raises_for_an_unknown_id(db_session):
    with pytest.raises(NoRuleException):
        id = uuid.uuid4()
        update_rule_status(db_session, id, RuleStatus.INACTIVE)


def test_update_rule_status_refuses_to_reactivate(db_session):
    _create_author(db_session)
    rule = _existing(db_session, RuleStatus.INACTIVE)

    with pytest.raises(InvalidRuleTransitionError):
        update_rule_status(db_session, rule.rule_id, RuleStatus.ACTIVE)
