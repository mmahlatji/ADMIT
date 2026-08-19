import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from enum import Enum
from sqlalchemy import DateTime, ForeignKey, Integer, String, Enum as SQLEnum, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class SourceType(Enum):
    ASR = "asr"
    UCT_MARKS = "uct_marks"
    MOTIVATIONS = "motivations"
    IT_TRANSCRIPTS = "it_transcripts"

class ImportStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"



class ImportRun(Base):
    __tablename__="import_runs"
    import_run_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    source_type: Mapped[SourceType] = mapped_column(SQLEnum(SourceType, name="source_types"), nullable=False, index=True)
    uploaded_by: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)) 
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ImportStatus] = mapped_column(SQLEnum(ImportStatus, name="import_status"), nullable=False, default=ImportStatus.PENDING, index=True)
    rows_total: Mapped[int] = mapped_column(Integer, nullable=False)
    rows_loaded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_auto_matched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_auto_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_flagged: Mapped[int] = mapped_column(Integer, nullable=False, default=0)



