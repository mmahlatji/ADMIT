"""
Responsible for generating a report on failed import rows
"""

import pandas as pd
from app.adapters.validation.rules import RULE_MESSAGES


def format_violations(violations: dict) -> dict:
    """
    Formats the violations dictionary into a summary that can be sent over
    the wire

    Returns:
        A dictionary in {rows: (a list of dictionaries containing the detals of the violation, row #, column name and message),
        summary: (dictionary containing summary of violations, total , violations and passed rows)}
    """
    frames = []
    masks = []

    for column, rule_violations in violations.items():
        for rule, mask in rule_violations.items():

            rows = mask[mask].index
            masks.append(mask)

            frames.append(
                {
                    "row": rows + 1,
                    "column": column.value,
                    "message": RULE_MESSAGES[rule],
                }
            )

    # generate summary statistics
    masks_df = pd.concat(masks, axis=1)
    total_rows = masks_df.shape[0]
    total_violations = sum(masks_df.any(axis=1))
    total_passed = total_rows - total_violations

    return {
        "rows": frames,
        "summary": {
            "total": total_rows,
            "violations": total_violations,
            "passed": total_passed,
        },
    }
