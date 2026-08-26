"""
Defines the possible validation rules that can be applied to critical columns
"""

from enum import Enum


class ValidationRules(Enum):
    NON_NULL = 1
    NUMERIC = 2
    EXACT_LENGTH = 3
    DUPLICATE = 4
    # TODO figure out how to pass exact length for ruleset


RULE_MESSAGES = {
    ValidationRules.NON_NULL: "This field is required.",
    ValidationRules.EXACT_LENGTH: "Invalid length.",
    ValidationRules.NUMERIC: "Must contain a numeric value.",
}
