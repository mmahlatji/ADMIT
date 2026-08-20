
from typing import Any
from enum import Enum
import uuid
from sqlalchemy import ForeignKey, Text, Enum as SQLEnum, UUID, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .matching_reviews import MatchingReview


class ValidationStatus(Enum):
    VALID = "valid"
    REJECTED = "rejected"

class Staging(Base):
    __tablename__="staging"
    staging_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    import_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("import_runs.import_run_id"), nullable=False)
    entity: Mapped[str] = mapped_column(String(50), nullable=False) # this will help with refering to the right table for insertions
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False) 
    normalized_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    validation_status: Mapped[ValidationStatus] = mapped_column(SQLEnum(ValidationStatus, name="validation_status"), nullable=False)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)
    matched_application_id: Mapped[str] = mapped_column(ForeignKey("applications.application_number"), nullable=True) # do we need this if asr has data about entire admission cycle
    matched_campus_id: Mapped[str] = mapped_column(ForeignKey("applications.campus_id"), nullable=True) # some data has no mapping to an application number eg. motivations
