from typing import TYPE_CHECKING
import uuid
from sqlalchemy import ForeignKey, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .applicants import Applicant


class Motivation(Base):
    __tablename__="motivations"
    motivation_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), unique=True, nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    motivation: Mapped[str] = mapped_column(Text, nullable=False)

    applicant: Mapped[Applicant] = relationship(back_populates="motivation")