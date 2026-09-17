import uuid

import pandas as pd
import pytest

from app.services.rule_engine import (
    Institution,
    RuleAction,
    RuleConflict,
    RuleEngine,
    RuleStatus,
    VariableError,
)


@pytest.fixture
def sample_applications():
    return pd.DataFrame({"campus_id": [1, 2, 3], "applied_date": ["2023-01-01"] * 3})


@pytest.fixture
def sample_marks():
    # Student 1: High performer
    # Student 2: Average performer
    # Student 3: Low performer
    # note that all marks are there, the rule engine trust marks source to filter out
    data = [
        {"campus_id": 1, "course_code": "csc2001f", "mark": 85},
        {"campus_id": 1, "course_code": "csc2002s", "mark": 90},
        {"campus_id": 1, "course_code": "csc3002f", "mark": 80},
        {"campus_id": 1, "course_code": "csc3003s", "mark": 88},
        {"campus_id": 2, "course_code": "csc2001f", "mark": 60},
        {"campus_id": 2, "course_code": "csc2002s", "mark": 55},
        {"campus_id": 2, "course_code": "csc3002f", "mark": 65},
        {"campus_id": 2, "course_code": "csc3003s", "mark": 60},
        {"campus_id": 3, "course_code": "csc2001f", "mark": 40},
        {"campus_id": 3, "course_code": "csc2002s", "mark": 45},
        {"campus_id": 3, "course_code": "csc3002f", "mark": 30},
        {"campus_id": 3, "course_code": "csc3003s", "mark": 35},
    ]
    return pd.DataFrame(data)


@pytest.fixture
def sample_marks_with_gaps(sample_marks):
    """Same as sample_marks but student 3 is missing csc3003s entirely."""
    marks = sample_marks.copy()
    return marks[
        ~((marks["campus_id"] == 3) & (marks["course_code"] == "csc3003s"))
    ].reset_index(drop=True)


@pytest.fixture
def empty_rules():
    return pd.DataFrame(
        columns=[
            "rule_id",
            "institution",
            "intake_year",
            "status",
            "rule",
            "rule_action",
        ]
    )


@pytest.fixture
def existing_rules():
    return pd.DataFrame(
        {
            "rule_id": [uuid.uuid4()],
            "institution": [Institution.UCT],
            "intake_year": [2024],
            "status": [RuleStatus.ACTIVE],
            "rule": ["csc2001f >= 50"],  # Students 1 & 2 pass this
            "rule_action": [RuleAction.ACCEPT],
        }
    )


@pytest.fixture
def reject_only_rules():
    """A single ACTIVE reject rule: students below 50 in csc2001f are rejected."""
    return pd.DataFrame(
        {
            "rule_id": [uuid.uuid4()],
            "institution": [Institution.UCT],
            "intake_year": [2024],
            "status": [RuleStatus.ACTIVE],
            "rule": ["csc2001f < 50"],  # Only Student 3 fails this
            "rule_action": [RuleAction.REJECT],
        }
    )


@pytest.fixture
def accept_and_reject_rules(existing_rules, reject_only_rules):
    """Non-overlapping accept + reject rules together, as apply_all_rules expects."""
    return pd.concat([existing_rules, reject_only_rules], ignore_index=True)


@pytest.fixture
def opposite_rules():
    """An ACTIVE rule with the opposite action, for opposite-conflict tests."""
    return pd.DataFrame(
        {
            "rule_id": [uuid.uuid4()],
            "institution": [Institution.UCT],
            "intake_year": [2024],
            "status": [RuleStatus.ACTIVE],
            "rule": ["csc2001f < 50"],
            "rule_action": [RuleAction.REJECT],
        }
    )


@pytest.fixture
def engine(sample_applications, sample_marks, empty_rules):
    return RuleEngine(sample_applications, sample_marks, empty_rules)


@pytest.fixture
def incomplete_only_rule():
    """
    Accept rule that needs csc3003s. Nobody in sample_marks actually meets the
    threshold, so paired with sample_marks_with_gaps this isolates the
    'missing the mark entirely' case from the 'has the mark but doesn't
    qualify' case.
    """
    return pd.DataFrame(
        {
            "rule_id": [uuid.uuid4()],
            "institution": [Institution.UCT],
            "intake_year": [2024],
            "status": [RuleStatus.ACTIVE],
            "rule": ["csc3003s >= 90"],
            "rule_action": [RuleAction.ACCEPT],
        }
    )


@pytest.fixture
def reject_rule_needs_csc3003s():
    """A reject rule nobody in the sample data actually falls afoul of, but which needs csc3003s."""
    return pd.DataFrame(
        {
            "rule_id": [uuid.uuid4()],
            "institution": [Institution.UCT],
            "intake_year": [2024],
            "status": [RuleStatus.ACTIVE],
            "rule": ["csc3003s < 20"],
            "rule_action": [RuleAction.REJECT],
        }
    )


@pytest.fixture
def accept_rule_and_reject_rule_needing_other_mark(
    existing_rules, reject_rule_needs_csc3003s
):
    """Accept rule on csc2001f + a non-overlapping reject rule that needs csc3003s."""
    return pd.concat([existing_rules, reject_rule_needs_csc3003s], ignore_index=True)


@pytest.fixture
def marks_accepted_despite_missing_other_mark(sample_marks_with_gaps):
    """
    Same as sample_marks_with_gaps (Student 3 missing csc3003s), but Student 1
    is also missing csc3003s — despite otherwise clearing csc2001f easily.
    """
    marks = sample_marks_with_gaps.copy()
    return marks[
        ~((marks["campus_id"] == 1) & (marks["course_code"] == "csc3003s"))
    ].reset_index(drop=True)


# --- TESTS ---


def test_pivot_marks(engine):
    """Test if marks are correctly reshaped into wide format"""
    pivoted = engine.marks

    assert "csc2001f" in pivoted.columns
    assert "csc2002s" in pivoted.columns

    # Check if student 1's marks mapped correctly
    student_1 = pivoted[pivoted["campus_id"] == 1].iloc[0]
    assert student_1["csc2001f"] == 85
    assert student_1["csc3003s"] == 88


def test_apply_expression_success(engine):
    """Test sympy successfully evaluates expression row-wise"""
    # Only Student 1 (85) and Student 2 (60) have >= 50
    results = engine.apply_expression("csc2001f >= 50")

    assert len(results) == 3
    assert results.iloc[0] == True  # Student 1
    assert results.iloc[1] == True  # Student 2
    assert results.iloc[2] == False  # Student 3


def test_apply_expression_invalid_syntax(engine):
    """Test invalid mathematical syntax raises an error"""
    with pytest.raises(VariableError, match="Invalid rule expression"):
        engine.apply_expression("csc2001f >=")  # Missing right hand side


def test_apply_expression_is_case_insensitive(engine):
    """
    _sanitize_expression lowercases input so convenors can type course codes
    in any case and still match the lowercased pivot columns.
    """
    lower = engine.apply_expression("csc2001f >= 50")
    upper = engine.apply_expression("CSC2001F >= 50")
    mixed = engine.apply_expression("Csc2001F >= 50")

    assert list(lower) == list(upper) == list(mixed)


# --- CONTRACT: _check_rule_conflicts takes expression and action as plain params ---


def test_check_rule_conflicts_missing_action_raises_typeerror(engine):
    """
    Regression guard: action is a required positional/keyword param now,
    not folded into a dict. Omitting it should fail loudly at the call site.
    """
    with pytest.raises(TypeError):
        engine._check_rule_conflicts(Institution.UCT, 2024, "csc2001f >= 50")


def test_check_rule_conflicts_first_rule(engine):
    """Test conflict checking when no active rules exist"""
    report = engine._check_rule_conflicts(
        Institution.UCT, 2024, "csc2001f >= 50", RuleAction.ACCEPT
    )

    assert report["first_rule"] is True
    assert "before" not in report
    assert list(report["after"]) == [True, True, False]


def test_check_rule_conflicts_with_existing(
    sample_applications, sample_marks, existing_rules
):
    """Test conflict checking with an existing active rule"""
    engine_with_rules = RuleEngine(sample_applications, sample_marks, existing_rules)

    # Existing rule is csc2001f >= 50 (Students 1 & 2 pass).
    # Proposed rule: csc2002s >= 80 (Only Student 1 passes).
    report = engine_with_rules._check_rule_conflicts(
        Institution.UCT, 2024, "csc2002s >= 80", RuleAction.ACCEPT
    )

    assert report["first_rule"] is False
    assert list(report["before"]) == [True, True, False]
    assert list(report["after"]) == [True, False, False]  # Student 2 drops out


def test_check_rule_conflicts_raises_conflict(
    sample_applications, sample_marks, existing_rules
):
    """Test engine raises RuleConflict if 0 applicants pass the new combination"""
    engine_with_rules = RuleEngine(sample_applications, sample_marks, existing_rules)

    # Existing rule: csc2001f >= 50
    # Proposed rule: csc2002s > 100 (Impossible, no one gets over 100 here)
    with pytest.raises(RuleConflict, match="No applicants satisfy all the rules"):
        engine_with_rules._check_rule_conflicts(
            Institution.UCT, 2024, "csc2002s > 100", RuleAction.ACCEPT
        )


def test_check_rule_conflicts_opposite_action_raises(
    sample_applications, sample_marks, opposite_rules
):
    """
    New coverage: an opposite-action active rule whose region overlaps the
    proposed rule's region should raise RuleConflict, independent of the
    same-action path.
    """
    engine_with_rules = RuleEngine(sample_applications, sample_marks, opposite_rules)

    # opposite_rules rejects csc2001f < 50; proposing to accept csc2001f >= 40
    # overlaps that region (40-50 band is claimed by both), so it should conflict.
    with pytest.raises(RuleConflict):
        engine_with_rules._check_rule_conflicts(
            Institution.UCT, 2024, "csc2001f >= 40", RuleAction.ACCEPT
        )


def test_generate_summary_first_rule(engine):
    """Test summary generation when it is the first rule being applied"""
    # 2 out of 3 pass
    report = {"first_rule": True, "after": pd.Series([True, True, False])}

    summary = engine._generate_summary(report)

    assert summary["first_rule"] is True
    assert summary["after"] == 2
    assert summary["pass_rate_after"] == (2 / 3) * 100


def test_generate_summary_decrease():
    """Test summary statistics when the proposed rule restricts admissions (decrease)"""
    # Mock an engine without needing full instantiation for this isolated test
    # Before: 2 pass. After: 1 passes. Total: 3.
    report = {
        "first_rule": False,
        "before": pd.Series([True, True, False]),
        "after": pd.Series([True, False, False]),
    }

    engine = RuleEngine.__new__(RuleEngine)
    summary = engine._generate_summary(report)

    assert summary["first_rule"] is False
    assert summary["before"] == 2
    assert summary["after"] == 1
    assert summary["pct_change"] == -50.0  # (1 - 2) / 2 * 100
    assert summary["pass_rate_before"] == (2 / 3) * 100
    assert summary["pass_rate_after"] == (1 / 3) * 100


def test_process_proposed_rule_e2e(sample_applications, sample_marks, existing_rules):
    """End-to-End test of the processing logic"""
    engine_with_rules = RuleEngine(sample_applications, sample_marks, existing_rules)

    summary = engine_with_rules.process_proposed_rule(
        institution=Institution.UCT,
        intake_year=2024,
        expression="csc2002s >= 80",
        action=RuleAction.ACCEPT,
    )

    assert summary["first_rule"] is False
    assert summary["before"] == 2
    assert summary["after"] == 1


# --- NEW METHOD: incomplete_for ---


def test_incomplete_for_no_missing_marks(engine):
    """When every applicant has the needed marks, nothing is incomplete."""
    assert engine.incomplete_for("csc2001f >= 50") == 0


def test_incomplete_for_missing_marks(sample_applications, sample_marks_with_gaps):
    """Applicants missing a required mark should be counted as incomplete."""
    engine = RuleEngine(
        sample_applications,
        sample_marks_with_gaps,
        pd.DataFrame(
            columns=[
                "rule_id",
                "institution",
                "intake_year",
                "status",
                "rule",
                "rule_action",
            ]
        ),
    )
    # Student 3 has no csc3003s mark at all
    assert engine.incomplete_for("csc3003s >= 50") == 1


# --- NEW METHOD: apply_all_rules (accepted / rejected / incomplete / pending split) ---
def _assert_partition(result: pd.DataFrame) -> None:
    """Every applicant must land in exactly one of the four buckets."""
    total = (
        result["accepted"].astype(int)
        + result["rejected"].astype(int)
        + result["incomplete"].astype(int)
        + result["pending"].astype(int)
    )
    assert (total == 1).all()


def test_apply_all_rules_columns_and_campus_ids(
    sample_applications, sample_marks, existing_rules
):
    engine_with_rules = RuleEngine(sample_applications, sample_marks, existing_rules)

    result = engine_with_rules.apply_all_rules(existing_rules)

    assert list(result.columns) == [
        "campus_id",
        "accepted",
        "rejected",
        "incomplete",
        "pending",
    ]
    assert list(result["campus_id"]) == [1, 2, 3]
    _assert_partition(result)


def test_apply_all_rules_only_accept_rules(
    sample_applications, sample_marks, existing_rules
):
    """
    Only an accept rule active: csc2001f >= 50 accepts Students 1 & 2.
    Student 3 has no reject rule against them, so they're pending, not rejected.
    """
    engine_with_rules = RuleEngine(sample_applications, sample_marks, existing_rules)

    result = engine_with_rules.apply_all_rules(existing_rules)

    assert list(result["accepted"]) == [True, True, False]
    assert list(result["rejected"]) == [False, False, False]
    assert list(result["incomplete"]) == [False, False, False]
    assert list(result["pending"]) == [False, False, True]
    _assert_partition(result)


def test_apply_all_rules_only_reject_rules(
    sample_applications, sample_marks, reject_only_rules
):
    """
    Only a reject rule active: csc2001f < 50 rejects Student 3.
    Students 1 & 2 have no accept rule for them, so they're pending, not accepted.
    """
    engine_with_rules = RuleEngine(sample_applications, sample_marks, reject_only_rules)

    result = engine_with_rules.apply_all_rules(reject_only_rules)

    assert list(result["accepted"]) == [False, False, False]
    assert list(result["rejected"]) == [False, False, True]
    assert list(result["incomplete"]) == [False, False, False]
    assert list(result["pending"]) == [True, True, False]
    _assert_partition(result)


def test_apply_all_rules_accept_and_reject_together(
    sample_applications, sample_marks, accept_and_reject_rules
):
    """
    Both an accept rule (csc2001f >= 50) and a non-overlapping reject rule
    (csc2001f < 50) active: every applicant should land in exactly one bucket,
    nobody left pending.
    """
    engine_with_rules = RuleEngine(
        sample_applications, sample_marks, accept_and_reject_rules
    )

    result = engine_with_rules.apply_all_rules(accept_and_reject_rules)

    assert list(result["accepted"]) == [True, True, False]
    assert list(result["rejected"]) == [False, False, True]
    assert list(result["incomplete"]) == [False, False, False]
    assert list(result["pending"]) == [False, False, False]
    # every applicant lands in exactly one bucket
    _assert_partition(result)


def test_apply_all_rules_empty_ruleset(engine, empty_rules):
    """No rules at all means nobody is accepted or rejected — everyone pending."""
    result = engine.apply_all_rules(empty_rules)

    assert list(result["accepted"]) == [False, False, False]
    assert list(result["rejected"]) == [False, False, False]
    assert list(result["incomplete"]) == [False, False, False]
    assert list(result["pending"]) == [True, True, True]
    _assert_partition(result)


# after adding incomplete...
def test_apply_all_rules_incomplete_bucket(
    sample_applications, sample_marks_with_gaps, incomplete_only_rule
):
    """
    The active rule needs csc3003s. Student 3 is missing that mark entirely,
    so they land in 'incomplete' — Students 1 & 2 have the mark but simply
    don't meet the >= 90 threshold, so they're genuinely 'pending', not
    incomplete.
    """
    engine_with_rules = RuleEngine(
        sample_applications, sample_marks_with_gaps, incomplete_only_rule
    )

    result = engine_with_rules.apply_all_rules(incomplete_only_rule)

    assert list(result["accepted"]) == [False, False, False]
    assert list(result["rejected"]) == [False, False, False]
    assert list(result["incomplete"]) == [False, False, True]
    assert list(result["pending"]) == [True, True, False]
    _assert_partition(result)


def test_apply_all_rules_accepted_takes_precedence_over_incomplete(
    sample_applications,
    marks_accepted_despite_missing_other_mark,
    accept_rule_and_reject_rule_needing_other_mark,
):
    """
    Student 1 clears the accept rule (csc2001f >= 50) but is missing
    csc3003s, which the separate, non-overlapping reject rule needs.
    Accepted is trivial and must win outright: Student 1 should never show
    up as incomplete just because an unrelated rule can't be evaluated for
    them.

    Student 3 is the mirror case on the undecided side: not accepted (40
    50), not rejected (missing csc3003s means that rule can't confirm
    rejection either), and IS missing csc3003s — so they land in
    'incomplete', not 'pending'.
    """
    engine_with_rules = RuleEngine(
        sample_applications,
        marks_accepted_despite_missing_other_mark,
        accept_rule_and_reject_rule_needing_other_mark,
    )

    result = engine_with_rules.apply_all_rules(
        accept_rule_and_reject_rule_needing_other_mark
    )
    by_campus = result.set_index("campus_id")

    assert by_campus.loc[1, "accepted"] == True
    assert by_campus.loc[1, "incomplete"] == False
    assert by_campus.loc[1, "pending"] == False

    assert by_campus.loc[3, "accepted"] == False
    assert by_campus.loc[3, "rejected"] == False
    assert by_campus.loc[3, "incomplete"] == True
    assert by_campus.loc[3, "pending"] == False

    _assert_partition(result)


# --- NEW HELPERS: _missing_for_expression / _missing_for_ruleset ---


def test_missing_for_expression_no_gaps(engine):
    missing = engine._missing_for_expression("csc2001f >= 50")
    assert list(missing) == [False, False, False]


def test_missing_for_expression_with_gaps(sample_applications, sample_marks_with_gaps):
    engine = RuleEngine(
        sample_applications,
        sample_marks_with_gaps,
        pd.DataFrame(
            columns=[
                "rule_id",
                "institution",
                "intake_year",
                "status",
                "rule",
                "rule_action",
            ]
        ),
    )
    missing = engine._missing_for_expression("csc3003s >= 50")
    assert list(missing) == [False, False, True]


def test_missing_for_ruleset_empty(engine, empty_rules):
    missing = engine._missing_for_ruleset(empty_rules)
    assert list(missing) == [False, False, False]


def test_missing_for_ruleset_no_rule_touches_the_gap(
    sample_applications, sample_marks_with_gaps, accept_and_reject_rules
):
    """
    accept_and_reject_rules only reference csc2001f, which nobody is missing —
    even though sample_marks_with_gaps has Student 3 missing csc3003s, that
    gap is irrelevant since no active rule needs csc3003s.
    """
    engine_with_rules = RuleEngine(
        sample_applications, sample_marks_with_gaps, accept_and_reject_rules
    )
    missing = engine_with_rules._missing_for_ruleset(accept_and_reject_rules)
    assert list(missing) == [False, False, False]


def test_missing_for_ruleset_true_if_any_rule_is_missing_its_mark(
    sample_applications,
    marks_accepted_despite_missing_other_mark,
    accept_rule_and_reject_rule_needing_other_mark,
):
    """
    Students 1 & 3 are both missing csc3003s, which the reject rule needs —
    even though they satisfy (or fail) the unrelated accept rule just fine.
    """
    engine_with_rules = RuleEngine(
        sample_applications,
        marks_accepted_despite_missing_other_mark,
        accept_rule_and_reject_rule_needing_other_mark,
    )
    missing = engine_with_rules._missing_for_ruleset(
        accept_rule_and_reject_rule_needing_other_mark
    )
    assert list(missing) == [True, False, True]


# --- NEW/underlying behavior: _evaluate_ruleset with no rules ---


def test_evaluate_ruleset_empty_returns_all_false(engine, empty_rules):
    decisions = engine._evaluate_ruleset(empty_rules)
    assert list(decisions) == [False, False, False]


# --- an institution with active rules but zero imported marks at all ---


def test_apply_all_rules_with_no_marks_at_all_does_not_crash(
    sample_applications, existing_rules
):
    """Before anyone's marks are imported for an institution, the marks query
    returns nothing and the caller builds an empty DataFrame from an empty
    list, which has no columns at all: not even campus_id. Pivoting that used
    to raise KeyError on course_code, so an institution with active rules but
    no marks yet crashed the whole apply_rules run instead of deciding
    nothing for it.
    """
    no_marks = pd.DataFrame([])

    engine_with_no_marks = RuleEngine(sample_applications, no_marks, existing_rules)
    result = engine_with_no_marks.apply_all_rules(existing_rules)

    assert list(result.columns) == [
        "campus_id",
        "accepted",
        "rejected",
        "incomplete",
        "pending",
    ]
    assert result.empty
