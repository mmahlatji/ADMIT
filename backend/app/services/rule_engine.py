from sympy.parsing.sympy_parser import parse_expr
import pandas as pd
import math
import re
from app.models.rules import Institution, RuleStatus

"""
 Rule eninge needs to show changes during run time, so we'll fetch the data once and manipulate it during run time
what the rule engine needs, all applications for that intake period (applications), all marks associated with currnet applications (marks), past rules implemented (rules)

fetch data from db -> load into a data frame -> parse application rule -> compare with previous rules -> no class -> apply rule creating new df (allows them to keep experimenting)> show summary statitics on rule
being applied -> confirm rule -> save rule



the flow is as follows: provide formula -> apply formula to loaded data -> supply summary statistics on how that change would affect decisions -> save rule if confimed
"""
ALLOWED_VARIABLES = ["csc2001f", "csc2002s", "csc3002f", "csc3003s"]
ALLOWED_OPERATIONS = [
    ">=",
    "<=",
    "**",
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


class VariableError(Exception):
    pass


class RuleConflict(Exception):
    pass


class RuleEngine:
    def __init__(
        self, applications: pd.DataFrame, marks: pd.DataFrame, rules: pd.DataFrame
    ):

        self.applications = applications
        self.marks = self._pivot_marks(marks)
        self.rules = rules

    def _sanitize_expression(self, expression: str) -> str:
        """
        Ensures the expression only contains values descriped in the allowed variable/operators

        Returns the expression lowercased, so it lines up with the lowercased
        pivot columns regardless of how the convenor typed the course code.
        """
        # course codes are stored uppercase (CSC2001F) but ALLOWED_VARIABLES and
        # the pivot columns are lowercase, and sympy symbols are case sensitive.
        # normalising here means either casing can be typed and still resolve.
        expression = expression.lower()
        expr = expression.replace(" ", "")
        operator_pattern = "|".join(map(re.escape, ALLOWED_OPERATIONS))
        split_expression = [x for x in re.split(operator_pattern, expr) if x]

        for var in split_expression:
            if var in ALLOWED_VARIABLES:
                continue

            try:
                value = float(var)
            except ValueError:
                raise VariableError(f"Variable/Opertor {var} is not recognized.")

            # float() also accepts nan/inf/1e999, which sail through the operator
            # check and then make every applicant pass. only real numbers here.
            if not math.isfinite(value):
                raise VariableError(f"Value {var} is not a finite number.")

        return expression

    def _pivot_marks(self, marks):
        """
        Changes shape of marks from mark_id | campus_id | course_code | mark ...  -> campus_id | csc2001f | csc2002s | csc3002f | csc3003s
        """
        marks = marks.copy()
        # lowercased to match ALLOWED_VARIABLES: the import pipeline writes
        # course_code uppercase, so without this the substitution silently
        # misses and bool() on the still-symbolic expression blows up.
        marks["course_code"] = marks["course_code"].str.lower()
        return marks.pivot(
            index="campus_id", columns="course_code", values="mark"
        ).reset_index()

    def _check_rule_conflicts(
        self, instituiton: Institution, intake_year: int, expression: str
    ) -> dict[str, pd.Series]:
        """
        Checks whether a new proposed decison rule conflicts with existing rules
        """
        filtered_rules = self.rules[
            (self.rules["institution"] == instituiton)
            & (self.rules["intake_year"] == intake_year)
            & (self.rules["status"] == RuleStatus.ACTIVE)
        ]

        if filtered_rules.empty:  # no currnet rules
            return {"first_rule": True, "after": self.apply_expression(expression)}

        rule_results = self.marks[["campus_id"]].copy()
        report = {"first_rule": False}

        for _, rule in filtered_rules.iterrows():
            rule_results[rule["rule_id"]] = self.apply_expression(rule["rule"])

        accepted = rule_results.drop(columns=["campus_id"]).all(axis=1)
        report["before"] = accepted
        rule_results["proposed"] = self.apply_expression(expression)
        post_accepted = rule_results.drop(columns=["campus_id"]).all(axis=1)

        if sum(post_accepted) == 0:
            raise RuleConflict("No applicants satisfy all the rules")

        report["after"] = post_accepted

        return report

    def _generate_summary(self, report: dict[str, pd.Series]):
        """
        Generates summary statistics as a result of a proposed new decision rule
        Returns:
            A dictionary in the form: {
                "first_rule":bool,
                "before": int,
                "after": int,
                "change": float,
                "pct_change": float,
                "rate_before": float,
                "rate_after": float,
            }
        """
        summary = {}
        total = report["after"].shape[0]

        if total == 0:
            raise ValueError("Cannot generate rule summary: no applicants found.")

        if not report["first_rule"]:
            summary["first_rule"] = False

            pre = sum(report["before"])
            post = sum(report["after"])

            summary["before"] = pre
            summary["after"] = post
            diff = post - pre
            summary["change"] = diff

            if pre == 0:
                summary["pct_change"] = None
            else:
                summary["pct_change"] = (diff / pre) * 100

            summary["pass_rate_before"] = (pre / total) * 100
            summary["pass_rate_after"] = (post / total) * 100

        else:
            accepted = sum(report["after"])
            summary["first_rule"] = True
            summary["after"] = accepted
            summary["pass_rate_after"] = (accepted / total) * 100

        return summary

    def apply_expression(self, expression: str):
        """
        Applies the expression to the current intake run of marks, then provides an admision summary
        `note we need to make sure that the marks provided in this stage are complete for the specified function`
        Args:
            expression: a mathematical expession in terms of course marks i.e 0.50*csc3003s+0.3*csc2002s+0.2*csc3002f>=80
        """

        # sympy's parse_expr reaches python builtins, so an unsanitized string
        # here is arbitrary code execution. sanitizing inside this method rather
        # than only in process_proposed_rule means every route to parse_expr goes
        # through the allow-list, including rules replayed from the db.
        expression = self._sanitize_expression(expression)

        try:
            expr = parse_expr(expression)
        except Exception as e:  # for now
            raise VariableError("Invalid rule expression") from e

        # does it matter if they see the actual applicants, or just the effects?
        proposed_decisions = self.marks.apply(
            lambda row: bool(expr.subs(row.to_dict())), axis=1
        )

        return proposed_decisions

    def process_proposed_rule(
        self, institution: Institution, intake_year: int, expression: str
    ):
        """
        Takes the proposed expression through the entire rule engine cycle
        """
        try:
            expression = self._sanitize_expression(expression)
        except VariableError:

            raise VariableError("Could not apply decision rule")

        conflict_report = self._check_rule_conflicts(
            instituiton=institution, intake_year=intake_year, expression=expression
        )

        summary = self._generate_summary(conflict_report)
        return summary
