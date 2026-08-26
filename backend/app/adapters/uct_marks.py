"""
The sheet adapter for the uct applicant marks sheet
"""

from app.adapters.base import BaseAdapter
from app.adapters.columns.uct_marks import (
    UCTMarksInputColumn,
    UCT_MARKS_CRITICAL_COLUMNS,
    UCT_MARKS_OUTPUT_COLUMNS,
)


class UCTMarkAdapter(BaseAdapter):
    input_columns = UCTMarksInputColumn
    critical_columns = UCT_MARKS_CRITICAL_COLUMNS
    output_columns = UCT_MARKS_OUTPUT_COLUMNS
