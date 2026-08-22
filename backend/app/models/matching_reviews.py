import uuid
from datetime import datetime, UTC
from enum import Enum
from typing import Any

from sqlalchemy import JSON, UUID, DateTime, ForeignKey, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MatchStatus(Enum):
    PENDING = "pending"
    RESOLVED = "resolved"

class MatchResolution(Enum):
    MERGE = "merge"
    REJECT = "reject"

class MatchingReview(Base):
    __tablename__="matching_reviews"
    match_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    staging_row_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("staging.staging_id"), nullable=False) # rem: if source_type then table
    candidate_keys: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True)
    match_signals: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True) # what matched
    status: Mapped[MatchStatus] = mapped_column(SQLEnum(MatchStatus, name="match_status"), nullable=False, default=MatchStatus.PENDING)
    resolved_by: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=True)
    resolution: Mapped[MatchResolution] = mapped_column(SQLEnum(MatchResolution, name="match_resolutions"), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(UTC))
