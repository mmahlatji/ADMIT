
from typing import Any
from enum import Enum
import uuid
from sqlalchemy import ForeignKey, Text, Enum as SQLEnum, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .import_runs import SourceType


class ValidationStatus(Enum):
    VALID = "valid"
    REJECTED = "rejected"

class Staging(Base):
    __tablename__="staging"
    staging_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    import_run_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("import_runs.import_run_id"), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(SQLEnum(SourceType, name="source_types"), nullable=False) # this will help with refering to the right table
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    normalized_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    validation_status: Mapped[ValidationStatus] = mapped_column(SQLEnum(ValidationStatus, name="validation_status"), nullable=False)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)
    matched_application_id: Mapped[str] = mapped_column(ForeignKey("applications.application_number"), nullable=True)
    matched_campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), nullable=True) # some data has no mapping to an application number eg. motivations

