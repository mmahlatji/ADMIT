"""
The sheet adapter for the IT applications processing
"""

from app.adapters.base import BaseAdapter
from app.adapters.columns.it_application import (
    ITApplicationInput,
    IT_APPLICATION_CRITICAL_COLUMNS,
    IT_APPLICATION_OUTPUT_COLUMNS,
)


class ITApplicationAdapter(BaseAdapter):
    input_columns = ITApplicationInput
    critical_columns = IT_APPLICATION_CRITICAL_COLUMNS
    output_columns = IT_APPLICATION_OUTPUT_COLUMNS
