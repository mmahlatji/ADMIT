from typing import NamedTuple

import sympy as sp
from scipy.optimize import linprog


class VariableError(Exception):
    pass


class RuleConflict(Exception):
    pass


class Actor(NamedTuple):
    employee_id: str


# Seeded by alembic/versions/d8f1c9a3e756_seed_the_system_user.py. This id
# has to match that migration exactly, or every automated decision fails
# the changed_by foreign key on system_logs.
SYSTEM_ACTOR = Actor(employee_id="0000001")

ALLOWED_VARIABLES = ["csc2001f", "csc2002s", "csc3002f", "csc3003s"]
ALLOWED_OPERATIONS = [
    ">=",
    "<=",
    ">",
    "<",
    "=",
    "+",
    "-",
    "/",
    "*",
    "(",
    ")",
]


def linearize(expr) -> tuple[dict[str, float], str, float]:
    """Converts the sympy relation into a format that can be used by the linear programming module (coeffs, sense, rhs)"""

    diff = sp.expand(expr.lhs - expr.rhs)  # move everything to one side

    # coeff(sym, 2) only ever caught an exact square: csc2001f**3 has a zero
    # coefficient at degree 2 (it is pure degree 3), so it passed this check
    # and then coeff(sym, 1) read 0 for it too, silently linearising the term
    # away instead of rejecting it. total_degree() catches any degree above 1,
    # and also a cross term like csc2001f*csc2002s that no single coeff() call
    # would see either.
    symbols = [sp.Symbol(v) for v in ALLOWED_VARIABLES]
    poly = diff.as_poly(*symbols)
    if poly is None or poly.total_degree() > 1:
        raise VariableError("Rule expression must be linear in the allowed variables")

    coeffs = {var: float(diff.coeff(sp.Symbol(var), 1)) for var in ALLOWED_VARIABLES}

    constant = float(diff.subs({sp.Symbol(v): 0 for v in ALLOWED_VARIABLES}))

    sense = ""

    # collapse all into closed regions for LP
    if isinstance(expr, (sp.Gt, sp.Ge)):
        sense = ">="
    elif isinstance(expr, (sp.Lt, sp.Le)):
        sense = "<="
    elif isinstance(expr, sp.Eq):
        sense = "="
    else:
        raise VariableError("Unsupported relations")

    return coeffs, sense, -constant


def regions_overlap(expr1, expr2) -> bool:
    """
    Checks wether a mark between 0-100 can actually exist for any given two expressions
    """
    variables = ALLOWED_VARIABLES

    A_ub, b_ub, A_eq, b_eq = [], [], [], []

    # convert each expresion into scipy format
    for expr in (expr1, expr2):
        coeffs, sense, rhs = linearize(expr)
        vec = [coeffs[v] for v in variables]
        if sense in ["<=", ">="]:
            lt = sense == "<="
            A_ub.append(vec if lt else [-c for c in vec])
            b_ub.append(rhs if lt else -rhs)
        else:
            A_eq.append(vec)
            b_eq.append(rhs)

    result = linprog(
        c=[0] * len(variables),
        A_ub=A_ub or None,
        b_ub=b_ub or None,
        A_eq=A_eq or None,
        b_eq=b_eq or None,
        bounds=[(0, 100)] * len(variables),
        method="highs",
    )

    return result.success
