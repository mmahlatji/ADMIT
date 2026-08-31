"""
Contains the input, output and critical column enum and dictionary for the IT application adapter
"""

from enum import Enum

from app.adapters.validation.rules import ValidationRules as vr


class ITApplicationInput(Enum):
    STUDENT_ID = "Student ID"
    CSC2001F = "CSC2001F"
    CSC2002S = "CSC2002S"
    CSC3002F = "CSC3002F"
    CSC3003S = "CSC3003S"


IT_APPLICATION_CRITICAL_COLUMNS = {ITApplicationInput.STUDENT_ID: [vr.NON_NULL]}


IT_APPLICATION_OUTPUT_COLUMNS = {
    ITApplicationInput.STUDENT_ID: "campus_id",
    ITApplicationInput.CSC2001F: "CSC2001F",
    ITApplicationInput.CSC3003S: "CSC3003S",
    ITApplicationInput.CSC2002S: "CSC2002S",
    ITApplicationInput.CSC3002F: "CSC3002F",
}
