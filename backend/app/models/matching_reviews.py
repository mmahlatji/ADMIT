import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Any
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Text, Enum as SQLEnum, JSON, UUID, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    resolved_by: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=False)
    resolution: Mapped[MatchResolution] = mapped_column(SQLEnum(MatchResolution), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())
