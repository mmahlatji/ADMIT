"""Direct tests for the LP-facing helpers in services/engine/tools.py.

linearize and regions_overlap had no coverage of their own before this: every
existing test drove them indirectly through RuleEngine, which never happened
to exercise a non-linear expression.
"""

import pytest
from sympy.parsing.sympy_parser import parse_expr

from app.services.engine.tools import VariableError, linearize, regions_overlap


def test_linearize_accepts_a_linear_expression():
    expr = parse_expr("0.5*csc2001f + 0.3*csc2002s >= 60")

    coeffs, sense, rhs = linearize(expr)

    assert coeffs["csc2001f"] == pytest.approx(0.5)
    assert coeffs["csc2002s"] == pytest.approx(0.3)
    assert coeffs["csc3002f"] == pytest.approx(0.0)
    assert sense == ">="
    assert rhs == pytest.approx(60)


def test_linearize_rejects_a_squared_term():
    expr = parse_expr("csc2001f**2 >= 50")

    with pytest.raises(VariableError):
        linearize(expr)


def test_linearize_rejects_a_cubed_term():
    """coeff(sym, 2) alone reads 0 for a pure cube, since none of its terms sit
    at degree exactly 2, so this used to sail through and silently linearise
    to a constraint of 0 >= 50 that matches nobody.
    """
    expr = parse_expr("csc2001f**3 >= 50")

    with pytest.raises(VariableError):
        linearize(expr)


def test_linearize_rejects_a_cross_term():
    """A product of two allowed variables is non-linear too, and coeff() on
    either symbol individually would not have caught it.
    """
    expr = parse_expr("csc2001f*csc2002s >= 50")

    with pytest.raises(VariableError):
        linearize(expr)


def test_regions_overlap_true_for_a_shared_range():
    lo = parse_expr("csc2001f >= 40")
    hi = parse_expr("csc2001f <= 60")

    assert regions_overlap(lo, hi) is True


def test_regions_overlap_false_for_disjoint_ranges():
    below = parse_expr("csc2001f <= 30")
    above = parse_expr("csc2001f >= 70")

    assert regions_overlap(below, above) is False
