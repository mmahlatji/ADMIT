"""
Contains the input, output and critical column enum and dictionary for the IT application adapter
"""

from app.adapters.validation.rules import ValidationRules as vr
from enum import Enum


class ITApplicationInput(Enum):
    STUDENT_ID = "Student ID"
    CSC2001F = "CSC2001F"
    CSC2002F = "CSC2002F"
    CSC3002F = "CSC3002F"
    CSC3003F = "CSC3003F"


IT_APPLICATION_CRITICAL_COLUMNS = {ITApplicationInput.STUDENT_ID: [vr.NON_NULL]}


IT_APPLICATION_OUTPUT_COLUMNS = {
    ITApplicationInput.STUDENT_ID: "campus_id",
    ITApplicationInput.CSC2001F: "CSC2001F",
    ITApplicationInput.CSC3003F: "CSC3003F",
    ITApplicationInput.CSC2002F: "CSC2002F",
    ITApplicationInput.CSC3002F: "CSC3002F",
}
