import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .applications import Application


class ProgramAction(str, Enum):
    PLACEHOLDER = "placeholder"

class ProgramReason(str, Enum):
    PLACEHOLDER = "placeholder"

class ProgramStatus(str, Enum):
    PLACEHOLDER = "placeholder"

class ApplicationLifecycle(Base):
    __tablename__="application_lifecycles"
    application_lifecycle_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    application_number: Mapped[str] = mapped_column(ForeignKey("applications.application_number"), unique=True, index=True, nullable=False)
    program_action: Mapped[ProgramAction] = mapped_column(SQLEnum(ProgramAction, name="program_action"), nullable=False)
    program_reason: Mapped[ProgramReason] = mapped_column(SQLEnum(ProgramReason, name="program_reason"), nullable=False) # may be nullable
    program_status: Mapped[ProgramStatus] = mapped_column(SQLEnum(ProgramStatus, name="program_status"), nullable=False) # may be nullable
    action_processed_by: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=False)
    action_processed_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="application_lifecycle")


