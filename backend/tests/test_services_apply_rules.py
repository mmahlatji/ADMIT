"""
Tests for app.services.rules.apply_rules

Strategy: apply_rules is orchestration around RuleEngine (already covered
in test_rule_engine.py) plus a handful of query calls and transition_status
side effects. Rather than hitting a real DB:

  1. Mock every query function and transition_status *at the import site
     inside app.services.rules* -- patch where the name is looked
     up, not where it's defined. This is the #1 way these tests silently
     no-op against the real DB instead of testing anything.
  2. Feed in lightweight fake ORM rows (SimpleNamespace) carrying only the
     attributes apply_rules / rules_to_df / RuleEngine actually read.
  3. Let the REAL RuleEngine run against that fake data. We're not
     re-testing its logic here, only that apply_rules wires
     rules/marks/applications into it correctly and reacts correctly to
     its output.
  4. Assert on transition_status.call_args / call_count instead of on any
     persisted DB state.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.models.applications import ApplicationStatus, DenyReason
from app.models.rules import Institution, RuleAction, RuleStatus
from app.services.rules import SYSTEM_ACTOR, NoRuleException, apply_rules

# --- fake row builders -------------------------------------------------


def make_rule(
    rule: str,
    rule_action: RuleAction,
    institution: Institution = Institution.UCT,
    status: RuleStatus = RuleStatus.ACTIVE,
    intake_year: int = 2024,
    rule_id: str = "r1",
):
    return SimpleNamespace(
        rule_id=rule_id,
        institution=institution,
        intake_year=intake_year,
        status=status,
        rule=rule,
        rule_action=rule_action,
    )


def make_application(
    campus_id: int,
    last_registration: str | None = "2022:SB001:reg",
    application_status: ApplicationStatus = ApplicationStatus.REVIEWED,
):
    return SimpleNamespace(
        campus_id=campus_id,
        last_registration=last_registration,
        application_status=application_status,
    )


def make_mark(campus_id: int, course_code: str, mark: float):
    return SimpleNamespace(campus_id=campus_id, course_code=course_code, mark=mark)


# --- shared dependency mocking ------------------------------------------


@pytest.fixture
def patched_deps():
    """Patches every external dependency apply_rules calls, yielding the mocks."""
    with patch("app.services.rules.rule_queries") as rule_queries, patch(
        "app.services.rules.application_queries"
    ) as application_queries, patch(
        "app.services.rules.mark_queries"
    ) as mark_queries, patch(
        "app.services.rules.transition_status"
    ) as transition_status:
        yield SimpleNamespace(
            rule_queries=rule_queries,
            application_queries=application_queries,
            mark_queries=mark_queries,
            transition_status=transition_status,
        )


# --- tests ---------------------------------------------------------------


def test_apply_rules_raises_when_no_institution_has_active_rules(patched_deps):
    """No active rules for any institution -> raise before touching applications at all."""
    patched_deps.rule_queries.get_active_rules.return_value = []

    with pytest.raises(NoRuleException, match="No current active rules for 2024"):
        apply_rules(db=MagicMock(), intake_year=2024)

    # should bail before ever fetching applications
    patched_deps.application_queries.get_applications_by_status_and_year.assert_not_called()


def test_apply_rules_skips_institution_without_rules(patched_deps):
    """UCT has a rule, OTHER doesn't -> apply UCT's rule, skip OTHER, no raise."""
    patched_deps.rule_queries.get_active_rules.side_effect = (
        lambda db, institution, year: (
            [make_rule("csc2001f >= 50", RuleAction.ACCEPT)]
            if institution == Institution.UCT
            else []
        )
    )
    app1 = make_application(campus_id=1, application_status=ApplicationStatus.REVIEWED)
    patched_deps.application_queries.get_applications_by_status_and_year.return_value = [
        app1
    ]
    patched_deps.mark_queries.get_applicant_marks_by_ids.return_value = [
        make_mark(1, "csc2001f", 85)
    ]

    db = MagicMock()
    apply_rules(db=db, intake_year=2024)

    patched_deps.transition_status.assert_called_once_with(
        db, SYSTEM_ACTOR, app1, ApplicationStatus.ACCEPTED
    )


def test_apply_rules_accepts_applicant_who_clears_accept_rule(patched_deps):
    patched_deps.rule_queries.get_active_rules.return_value = [
        make_rule("csc2001f >= 50", RuleAction.ACCEPT)
    ]
    app1 = make_application(campus_id=1, application_status=ApplicationStatus.REVIEWED)
    patched_deps.application_queries.get_applications_by_status_and_year.return_value = [app1]
    patched_deps.mark_queries.get_applicant_marks_by_ids.return_value = [
        make_mark(1, "csc2001f", 85)
    ]

    db = MagicMock()
    apply_rules(db=db, intake_year=2024)

    patched_deps.transition_status.assert_called_once_with(
        db, SYSTEM_ACTOR, app1, ApplicationStatus.ACCEPTED
    )


def test_apply_rules_rejects_applicant_who_fails_reject_rule(patched_deps):
    patched_deps.rule_queries.get_active_rules.return_value = [
        make_rule("csc2001f < 50", RuleAction.REJECT)
    ]
    app3 = make_application(campus_id=3, application_status=ApplicationStatus.REVIEWED)
    patched_deps.application_queries.get_applications_by_status_and_year.return_value = [app3]
    patched_deps.mark_queries.get_applicant_marks_by_ids.return_value = [
        make_mark(3, "csc2001f", 40)
    ]

    db = MagicMock()
    apply_rules(db=db, intake_year=2024)

    patched_deps.transition_status.assert_called_once_with(
        db,
        SYSTEM_ACTOR,
        app3,
        ApplicationStatus.DENIED,
        DenyReason.REQUIREMENTS_NOT_MET,
    )


def test_apply_rules_moves_pending_applied_applicant_to_reviewed(patched_deps):
    """
    Rule needs csc2001f (present, 85) but sets the bar at 90 -> not accepted.
    No reject rule active -> not rejected. Not missing any mark -> pending,
    not incomplete. Starting status APPLIED -> should be bumped to REVIEWED.
    """
    patched_deps.rule_queries.get_active_rules.return_value = [
        make_rule("csc2001f >= 90", RuleAction.ACCEPT)
    ]
    app2 = make_application(campus_id=2, application_status=ApplicationStatus.APPLIED)
    patched_deps.application_queries.get_applications_by_status_and_year.return_value = [app2]
    patched_deps.mark_queries.get_applicant_marks_by_ids.return_value = [
        make_mark(2, "csc2001f", 85)
    ]

    db = MagicMock()
    apply_rules(db=db, intake_year=2024)

    patched_deps.transition_status.assert_called_once_with(
        db, SYSTEM_ACTOR, app2, ApplicationStatus.REVIEWED
    )


def test_apply_rules_leaves_pending_non_applied_applicant_untouched(patched_deps):
    """Same pending scenario, but the applicant is already REVIEWED -> no transition call."""
    patched_deps.rule_queries.get_active_rules.return_value = [
        make_rule("csc2001f >= 90", RuleAction.ACCEPT)
    ]
    app2 = make_application(campus_id=2, application_status=ApplicationStatus.REVIEWED)
    patched_deps.application_queries.get_applications_by_status_and_year.return_value = [app2]
    patched_deps.mark_queries.get_applicant_marks_by_ids.return_value = [
        make_mark(2, "csc2001f", 85)
    ]

    apply_rules(db=MagicMock(), intake_year=2024)

    patched_deps.transition_status.assert_not_called()


def test_apply_rules_leaves_incomplete_applicant_untouched(patched_deps):
    """
    Rule needs csc3003s; applicant has some marks but not that one, so the
    rule can't be evaluated for them -> incomplete. Even though they came
    in as APPLIED, incomplete applicants should NOT be bumped to REVIEWED --
    there's nothing to review yet.
    """
    patched_deps.rule_queries.get_active_rules.return_value = [
        make_rule("csc3003s >= 50", RuleAction.ACCEPT)
    ]
    app1 = make_application(campus_id=1, application_status=ApplicationStatus.APPLIED)
    patched_deps.application_queries.get_applications_by_status_and_year.return_value = [app1]
    # has a mark, just not the one the rule needs -- avoids an entirely
    # empty marks DataFrame, which is a separate edge case (see note below)
    patched_deps.mark_queries.get_applicant_marks_by_ids.return_value = [
        make_mark(1, "csc2001f", 85)
    ]

    apply_rules(db=MagicMock(), intake_year=2024)

    patched_deps.transition_status.assert_not_called()


def test_apply_rules_applies_rules_per_institution_independently(patched_deps):
    """
    Each institution's rule should only ever be evaluated against that
    institution's own applicants -- a UCT rule must not reach an OTHER
    applicant and vice versa.
    """
    patched_deps.rule_queries.get_active_rules.side_effect = (
        lambda db, institution, year: [
            make_rule("csc2001f >= 50", RuleAction.ACCEPT, institution=institution)
        ]
    )
    uct_app = make_application(
        campus_id=1,
        last_registration="2022:SB001:reg",
        application_status=ApplicationStatus.REVIEWED,
    )
    other_app = make_application(
        campus_id=2,
        last_registration="",
        application_status=ApplicationStatus.REVIEWED,
    )
    patched_deps.application_queries.get_applications_by_status_and_year.return_value = [
        uct_app,
        other_app,
    ]
    patched_deps.mark_queries.get_applicant_marks_by_ids.return_value = [
        make_mark(1, "csc2001f", 85),
        make_mark(2, "csc2001f", 85),
    ]

    db = MagicMock()
    apply_rules(db=db, intake_year=2024)

    assert patched_deps.transition_status.call_count == 2
    patched_deps.transition_status.assert_any_call(
        db, SYSTEM_ACTOR, uct_app, ApplicationStatus.ACCEPTED
    )
    patched_deps.transition_status.assert_any_call(
        db, SYSTEM_ACTOR, other_app, ApplicationStatus.ACCEPTED
    )


def test_apply_rules_does_not_transition_when_accept_and_reject_both_fire(
    patched_deps,
):
    """An accept rule and a reject rule can both be satisfied by the same
    applicant if they were saved at different times and never checked
    against each other (the conflict check only runs when a rule is first
    proposed). apply_rules used to resolve that silently in favour of
    accept, so nobody could tell the two rules actually disagreed about
    this applicant. It should leave them alone instead.
    """
    patched_deps.rule_queries.get_active_rules.return_value = [
        make_rule("csc2001f >= 50", RuleAction.ACCEPT, rule_id="r1"),
        make_rule("csc2002s < 100", RuleAction.REJECT, rule_id="r2"),
    ]
    app1 = make_application(campus_id=1, application_status=ApplicationStatus.REVIEWED)
    patched_deps.application_queries.get_applications_by_status_and_year.return_value = [
        app1
    ]
    patched_deps.mark_queries.get_applicant_marks_by_ids.return_value = [
        make_mark(1, "csc2001f", 85),
        make_mark(1, "csc2002s", 90),
    ]

    db = MagicMock()
    apply_rules(db=db, intake_year=2024)

    patched_deps.transition_status.assert_not_called()


def test_apply_rules_does_not_crash_when_nobody_has_marks_yet(patched_deps):
    """Before any marks have been imported for the intake at all, the marks
    query returns nothing and the DataFrame built from it used to have no
    columns, so the campus_id filter raised KeyError before a single
    institution was even tried.
    """
    patched_deps.rule_queries.get_active_rules.return_value = [
        make_rule("csc2001f >= 50", RuleAction.ACCEPT)
    ]
    app1 = make_application(campus_id=1, application_status=ApplicationStatus.REVIEWED)
    patched_deps.application_queries.get_applications_by_status_and_year.return_value = [
        app1
    ]
    patched_deps.mark_queries.get_applicant_marks_by_ids.return_value = []

    db = MagicMock()
    apply_rules(db=db, intake_year=2024)  # must not raise

    patched_deps.transition_status.assert_not_called()
