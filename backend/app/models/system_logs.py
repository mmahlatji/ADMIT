from datetime import datetime, UTC
from enum import Enum
from typing import Dict, Any
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.deps import Base


class ChangeSource(Enum):
    IMPORT = "import"
    MANUAL_EDIT = "manual_edit"
    MERGE_RESOLUTION = "merge_resolution"
    RULES_CALC = "rules_calc"
    DECISION = "decision"

class SystemLog(Base): 
    __tablename__ = "system_logs"
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String)
    old_data: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    new_data: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    changed_by: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    reason: Mapped[ChangeSource] = mapped_column(SQLEnum(ChangeSource, name="change_source"))
    import_run_id: Mapped[str] = mapped_column(String(10), nullable=True)



"""
The audit table does not have to refer to another row in some table we just need to be able to group related logs by an id
and we will perform the proper type conversion to link the applicants/applications to a log
"""