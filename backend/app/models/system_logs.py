import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, UUID, DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ChangeSource(Enum):
    IMPORT = "import"
    MANUAL_EDIT = "manual_edit"
    MERGE_RESOLUTION = "merge_resolution"
    RULES_CALC = "rules_calc"
    DECISION = "decision"

class SystemLog(Base): 
    __tablename__ = "system_logs"
    log_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    entity_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)
    # was JSONB (postgres-only), SQLite can't compile that type and our tests run on SQLite
    old_data: Mapped[dict[str, Any]] = mapped_column(JSON)
    new_data: Mapped[dict[str, Any]] = mapped_column(JSON)
    changed_by: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reason: Mapped[ChangeSource] = mapped_column(SQLEnum(ChangeSource, name="change_source"))
    import_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("import_runs.import_run_id"), nullable=True)
