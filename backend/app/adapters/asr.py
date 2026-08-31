"""
The sheet adapter for the asr document
"""

from app.adapters.base import BaseAdapter
from app.adapters.columns.asr import (
    ASR_CRITICAL_COLUMNS,
    ASR_OUTPUT_COLUMNS,
    ASRInputColumn,
)


class ASRAdapter(BaseAdapter):
    input_columns = ASRInputColumn
    critical_columns = ASR_CRITICAL_COLUMNS
    output_columns = ASR_OUTPUT_COLUMNS
