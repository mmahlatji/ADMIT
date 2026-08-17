from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.deps import Base

from .applications import Application


class ProgramAction(Enum):
    pass

class ProgramReason(Enum):
    pass

class ProgramStatus(Enum):
    pass

class ApplicationLifecycle(Base):
    __tablename__="application_lifecycles"
    application_number: Mapped[str] = mapped_column(ForeignKey("applicantions.application_number"), primary_key=True, index=True)
    program_action: Mapped[ProgramAction] = mapped_column(SQLEnum(ProgramAction, name="program_action"), nullable=False)
    program_reason: Mapped[ProgramReason] = mapped_column(SQLEnum(ProgramReason, name="program_reason"), nullable=False) # may be nullable
    program_status: Mapped[ProgramStatus] = mapped_column(SQLEnum(ProgramStatus, name="program_status"), nullable=False) # may be nullable
    action_processed_by: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=False)
    action_processed_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    application: Mapped["Application"] = relationship(back_populates="application_lifecycle")


