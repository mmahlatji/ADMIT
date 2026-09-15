import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import UUID, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Institution(Enum): 
    UCT = "University of Cape Town"
    UJ = "University of Johannesburg"


class RuleStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"

class RuleAction(str, Enum):
    REJECT = "reject"  # Deny Requirements Not Met
    ACCEPT = "accept"   # Accept 


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
    rule_action: Mapped[RuleAction] = mapped_column(
            SQLEnum(RuleAction, name="rule_action" ), nullable=False
        )
    # str, not uuid: users.employee_id is a String(7), not the user's uuid pk
    created_by: Mapped[str] = mapped_column(
        ForeignKey("users.employee_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
