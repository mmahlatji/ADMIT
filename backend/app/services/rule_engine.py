import math
import re

import pandas as pd
from sympy.parsing.sympy_parser import parse_expr

from app.models.rules import Institution, RuleAction, RuleStatus
from app.services.engine.tools import (
    ALLOWED_OPERATIONS,
    ALLOWED_VARIABLES,
    RuleConflict,
    VariableError,
    regions_overlap,
)

"""
 Rule eninge needs to show changes during run time, so we'll fetch the data once and manipulate it during run time
what the rule engine needs, all applications for that intake period (applications), all marks associated with currnet applications (marks), past rules implemented (rules)

fetch data from db -> load into a data frame -> parse application rule -> compare with previous rules -> no class -> apply rule creating new df (allows them to keep experimenting)> show summary statitics on rule
being applied -> confirm rule -> save rule



the flow is as follows: provide formula -> apply formula to loaded data -> supply summary statistics on how that change would affect decisions -> save rule if confimed
"""


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

            if not math.isfinite(value):
                raise VariableError(f"Value {var} is not a finite number.")

        return expression

    def apply_all_rules(self, rules: pd.DataFrame) -> pd.DataFrame:
        """Evaluates self.rules against self.marks. Returns campus_id + accepted."""

        accept_rules = rules[rules["rule_action"] == RuleAction.ACCEPT]
        reject_rules = rules[rules["rule_action"] == RuleAction.REJECT]

        result = self.marks[["campus_id"]].copy()
        result["accepted"] = self._evaluate_ruleset(accept_rules)
        result["rejected"] = self._evaluate_ruleset(reject_rules)

        undecided = ~(result["accepted"] | result["rejected"])
        missing = self._missing_for_ruleset(rules)

        result["incomplete"] = undecided & missing
        result["pending"] = undecided & ~missing
        return result

    def _pivot_marks(self, marks):
        """
        Changes shape of marks from mark_id | campus_id | course_code | mark ...  -> campus_id | csc2001f | csc2002s | csc3002f | csc3003s
        """
        if marks.empty:
            # No marks imported yet for this institutions applicants at all, so
            # there is no course_code column to pivot on. Every rule then needs
            # a mark it does not have, which the rest of the engine already
            # handles correctly once there is a campus_id column to key on.
            return pd.DataFrame(columns=["campus_id"])
        marks = marks.copy()
        marks["course_code"] = marks["course_code"].str.lower()
        return marks.pivot(
            index="campus_id", columns="course_code", values="mark"
        ).reset_index()

    def _check_opposite_action_conflicts(
        self, active_rules: pd.DataFrame, expression: str, action: RuleAction
    ):

        opposite_action_rules = active_rules[
            active_rules["rule_action"] == action.opposite
        ]

        if opposite_action_rules.empty:
            return False

        has_conflicts = bool(
            pd.Series(
                [
                    regions_overlap(
                        parse_expr(opposite_rule["rule"]),
                        parse_expr(expression),  # safe here
                    )
                    for _, opposite_rule in opposite_action_rules.iterrows()
                ]
            ).any()
        )

        return has_conflicts

    def _check_same_action_conficts(
        self, active_rules: pd.DataFrame, expression: str, action: RuleAction
    ):

        same_action_rules = active_rules[active_rules["rule_action"] == action]

        if same_action_rules.empty:  # no current rule with specified action
            return {
                "first_rule": True,
                "after": self.apply_expression(expression),
            }

        accepted_before = self._evaluate_ruleset(same_action_rules)
        accepted_after = accepted_before & self.apply_expression(expression)

        if sum(accepted_after) == 0:
            raise RuleConflict("No applicants satisfy all the rules")

        return {"first_rule": False, "before": accepted_before, "after": accepted_after}

    def _check_rule_conflicts(
        self,
        instituiton: Institution,
        intake_year: int,
        expression: str,
        action: RuleAction,
    ) -> dict[str, pd.Series]:
        """
        Checks whether a new proposed decison rule conflicts with existing rules

        """

        # check confilcts with opposite rules, you cannot have a case of True True for both accept and reject
        # which means there is a logical conflict, this needs to be tested across the marks domain 0-100
        # we use linear programming feasibility

        active_rules = self.rules[
            (self.rules["institution"] == instituiton)
            & (self.rules["intake_year"] == intake_year)
            & (self.rules["status"] == RuleStatus.ACTIVE)
        ]

        has_opposite_conflicts = self._check_opposite_action_conflicts(
            active_rules, expression, action
        )

        if has_opposite_conflicts:
            raise RuleConflict(
                f"The new rule expression = {expression}, action = {action.value} causes conflicts with other {action.opposite.value} existing rules"
            )

        try:

            report = self._check_same_action_conficts(active_rules, expression, action)

        except RuleConflict as e:
            raise RuleConflict(e)

        return report

    def _evaluate_ruleset(self, rules: pd.DataFrame) -> pd.Series:
        """Returns a boolean Series: True where every rule in `rules` passes."""
        if rules.empty:
            return pd.Series(False, index=self.marks.index)
        decisions = pd.DataFrame(
            {
                rule["rule_id"]: self.apply_expression(rule["rule"])
                for _, rule in rules.iterrows()
            }
        )
        return decisions.all(axis=1)

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

        expression = self._sanitize_expression(expression)

        try:
            expr = parse_expr(expression)
        except Exception as e:  # for now
            raise VariableError("Invalid rule expression") from e

        needed = {str(symbol) for symbol in expr.free_symbols}

        def decide(row):
            values = row.to_dict()
            if any(pd.isna(values.get(name)) for name in needed):
                return False
            return bool(expr.subs(values))

        proposed_decisions = self.marks.apply(decide, axis=1)

        return proposed_decisions

    def _missing_for_expression(self, expression: str) -> pd.Series:
        """Creates a boolean series, True where the applicant lacks a mark this expression needs."""
        expr = parse_expr(self._sanitize_expression(expression))
        needed = {str(symbol) for symbol in expr.free_symbols}
        missing_cols = [name for name in needed if name not in self.marks.columns]
        if missing_cols:
            return pd.Series(True, index=self.marks.index)
        return self.marks[list(needed)].isna().any(axis=1)

    def incomplete_for(self, expression: str) -> int:
        """How many applicants lack a mark the expression needs."""
        return int(self._missing_for_expression(expression).sum())

    def _missing_for_ruleset(self, rules: pd.DataFrame) -> pd.Series:
        """Creates a boolean series, True where the applicant lacks a mark needed by ANY rule in `rules`."""
        if rules.empty:
            return pd.Series(False, index=self.marks.index)
        missing = pd.DataFrame(
            {
                rule["rule_id"]: self._missing_for_expression(rule["rule"])
                for _, rule in rules.iterrows()
            }
        )
        return missing.any(axis=1)

    def process_proposed_rule(
        self,
        institution: Institution,
        intake_year: int,
        expression: str,
        action: RuleAction,
    ):
        """
        Takes the proposed expression through the entire rule engine cycle
        """
        try:
            expression = self._sanitize_expression(expression)
            conflict_report = self._check_rule_conflicts(
                instituiton=institution,
                intake_year=intake_year,
                expression=expression,
                action=action,
            )
            summary = self._generate_summary(conflict_report)
            return summary
        except VariableError:

            raise VariableError("Could not apply decision rule")
        except RuleConflict as e:
            raise RuleConflict(e)
