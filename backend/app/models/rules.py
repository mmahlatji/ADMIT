import uuid
from datetime import datetime
from sqlalchemy import UUID, UniqueConstraint, ForeignKey, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SQLEnum


from .base import Base
from enum import Enum


class Institution(Enum):
    UCT = "University of Cape Town"
    UJ = "University of Johannesburg"


class RuleStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


class Rules(Base):
    __tablename__ = "rules"
    __table_args__ = (
        UniqueConstraint(
            "institution",
            "intake_year",
            "version",
            name="uq_rule_institution_year_version",
        ),
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    institution: Mapped[Institution] = mapped_column(
        SQLEnum(Institution, name="institution"), nullable=False
    )
    intake_year: Mapped[int] = mapped_column(nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    rule: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[RuleStatus] = mapped_column(
        SQLEnum(RuleStatus, name="status"), nullable=False
    )
    # str, not uuid: users.employee_id is a String(7), not the user's uuid pk
    created_by: Mapped[str] = mapped_column(
        ForeignKey("users.employee_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
