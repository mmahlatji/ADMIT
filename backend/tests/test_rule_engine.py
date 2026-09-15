import uuid

import pandas as pd
import pytest

from app.services.rule_engine import (
    Institution,
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
def empty_rules():
    return pd.DataFrame(
        columns=["rule_id", "institution", "intake_year", "status", "rule"]
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
        }
    )


@pytest.fixture
def engine(sample_applications, sample_marks, empty_rules):
    return RuleEngine(sample_applications, sample_marks, empty_rules)


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


def test_check_rule_conflicts_first_rule(engine):
    """Test conflict checking when no active rules exist"""
    report = engine._check_rule_conflicts(Institution.UCT, 2024, "csc2001f >= 50")

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
        Institution.UCT, 2024, "csc2002s >= 80"
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
        engine_with_rules._check_rule_conflicts(Institution.UCT, 2024, "csc2002s > 100")


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

    # End-to-end check
    summary = engine_with_rules.process_proposed_rule(
        institution=Institution.UCT, intake_year=2024, expression="csc2002s >= 80"
    )

    assert summary["first_rule"] is False
    assert summary["before"] == 2
    assert summary["after"] == 1
