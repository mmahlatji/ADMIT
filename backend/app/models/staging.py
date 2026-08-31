import uuid
from enum import Enum
from typing import Any

from sqlalchemy import JSON, UUID, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ValidationStatus(Enum):
    VALID = "valid"
    REJECTED = "rejected"
    PENDING = "pending"


class Staging(Base):
    __tablename__ = "staging"
    staging_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    import_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("import_runs.import_run_id"), nullable=False, index=True)
    entity: Mapped[str] = mapped_column(String(50), nullable=False) # this will help with refering to the right table for insertions
    # was JSONB (postgres-only), SQLite can't compile that type and our tests run on SQLite
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    normalized_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    validation_status: Mapped[ValidationStatus] = mapped_column(SQLEnum(ValidationStatus, name="validation_status"), nullable=False, index=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)
    matched_application_id: Mapped[str] = mapped_column(
        ForeignKey("applications.application_number"), nullable=True
    )  # do we need this if asr has data about entire admission cycle
    matched_campus_id: Mapped[str] = mapped_column(
        ForeignKey("applicants.campus_id"), nullable=True
    )  # some data has no mapping to an application number eg. motivations
