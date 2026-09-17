import pandas as pd
import pytest

from app.services.engine.tools import VariableError
from app.services.rule_engine import RuleEngine


@pytest.fixture
def parser():
    data = [
        {"campus_id": 1, "course_code": "csc2001f", "mark": 85},
    ]
    return RuleEngine(pd.DataFrame([]), pd.DataFrame(data), pd.DataFrame())


def test_valid_expression(parser):
    expression = "(csc3003s * 0.5)/20 + csc2002s * 0.5 >= 60"

    result = parser._sanitize_expression(expression)

    assert result == expression


def test_invalid_variable(parser):
    expression = "csc3003s * 0.5 + hello * 0.5 >= 60"

    with pytest.raises(VariableError):
        parser._sanitize_expression(expression)


def test_invalid_number(parser):
    expression = "csc3003s * abc >= 60"

    with pytest.raises(VariableError):
        parser._sanitize_expression(expression)


def test_invalid_operator(parser):
    expression = "csc3003s @ 50"

    with pytest.raises(VariableError):
        parser._sanitize_expression(expression)


def test_uppercase_course_codes_are_accepted(parser):
    # the import pipeline stores course_code uppercase, so a convenor copying a
    # code straight out of the marks sheet must still be recognised
    result = parser._sanitize_expression("CSC3003S * 0.5 >= 60")

    assert result == "csc3003s * 0.5 >= 60"


@pytest.mark.parametrize("value", ["nan", "inf", "1e999"])
def test_non_finite_values_rejected(parser, value):
    # float() accepts all of these, and they make every applicant pass
    with pytest.raises(VariableError):
        parser._sanitize_expression(f"csc3003s >= {value}")


def test_apply_expression_sanitizes_its_own_input(parser):
    # parse_expr reaches python builtins, so every route into it has to go
    # through the allow-list, not just process_proposed_rule
    with pytest.raises(VariableError):
        parser.apply_expression("__import__('os').getcwd()")
