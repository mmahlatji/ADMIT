"""
Contains the input, output and critical column enum and dictionary for the motivations adapter
"""

from enum import Enum

from app.adapters.validation.rules import ValidationRules as vr


class MotivationsInputColumn(Enum):
    STUDENT_ID = "UCT studentID"
    TEXT = "Motivation for acceptance into Computer Science Honours"
    # ommited name and surname, motivation is sent from a student who has an application on record, no need for redundancy, opinions?


MOTIVATIONS_CRITICAL_COLUMNS = {
    MotivationsInputColumn.STUDENT_ID: [vr.NON_NULL],
}


MOTIVATIONS_OUTPUT_COLUMNS = {
    MotivationsInputColumn.STUDENT_ID: "campus_id",
    MotivationsInputColumn.TEXT: "motivation",
}
