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
    from .users import User

class VoteDecision(str, Enum):
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"


class Vote(Base):
    __tablename__="votes"
    vote_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    application_number: Mapped[str] = mapped_column(ForeignKey("applications.application_number"), primary_key=True,nullable=False, index=True)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), nullable=False)
    vote: Mapped[VoteDecision] = mapped_column(SQLEnum(VoteDecision, name="vote_decision", values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False)
    voter_id: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=False)
    voted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="votes", foreign_keys=[application_number])
    voter: Mapped["User"] = relationship(back_populates="votes")