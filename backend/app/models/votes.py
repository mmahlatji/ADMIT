import uuid
from enum import Enum
from datetime import date, datetime, timezone
from sqlalchemy import Float, ForeignKey, DateTime, String, Text, UUID, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.deps import Base
from .applications import Application

class VoteDecision(Enum):
    pass


class Vote(Base):
    __tablename__="votes"
    vote_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    application_number: Mapped[str] = mapped_column(ForeignKey("applications.application_number"), nullable=False, index=True)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), nullable=False)
    vote: Mapped[VoteDecision] = mapped_column(SQLEnum(VoteDecision, name="vote_decision"), nullable=False)
    voter_id: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=False)
    voted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    application: Mapped["Application"] = relationship(back_populates="votes")
    # voter