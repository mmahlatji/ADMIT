"""
The sheet adapter for the motivations sheet
"""

from app.adapters.base import BaseAdapter
from app.adapters.columns.motivations import (
    MotivationsInputColumn,
    MOTIVATIONS_CRITICAL_COLUMNS,
    MOTIVATIONS_OUTPUT_COLUMNS,
)


class MotivationsAdapter(BaseAdapter):
    input_columns = MotivationsInputColumn
    critical_columns = MOTIVATIONS_CRITICAL_COLUMNS
    output_columns = MOTIVATIONS_OUTPUT_COLUMNS
