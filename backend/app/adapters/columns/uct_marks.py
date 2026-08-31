"""
Contains the input, output and critical column enum and dictionary for the uct marks document adapter
"""

from enum import Enum

from app.adapters.validation.rules import ValidationRules as vr


class UCTMarksInputColumn(Enum):
    STUDENT_ID = "Student ID"
    CSC2001F = "CSC2001F"
    CSC2002S = "CSC2002S"
    CSC3002F = "CSC3002F"
    CSC3003S = "CSC3003S"


UCT_MARKS_CRITICAL_COLUMNS = {UCTMarksInputColumn.STUDENT_ID: [vr.NON_NULL]}

"""Since a document like UCT marks is going to be normalized, we will have to follow a different convention
for any sheet that will need normalization, the mapping remain input_col: output_name, however for sheets still needing normalization,
the field will remain as ingested and handled in the normalization layer. d
"""
UCT_MARKS_OUTPUT_COLUMNS = {
    UCTMarksInputColumn.STUDENT_ID: "campus_id",
    UCTMarksInputColumn.CSC2001F: "CSC2001F",
    UCTMarksInputColumn.CSC2002S: "CSC2002S",
    UCTMarksInputColumn.CSC3002F: "CSC3002F",
    UCTMarksInputColumn.CSC3003S: "CSC3003S",
}
