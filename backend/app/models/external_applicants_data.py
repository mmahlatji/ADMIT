import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .applications import Application




class ExternalApplicantData(Base):
    __tablename__="external_applicants_data"
    ea_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    application_number: Mapped[str] = mapped_column(ForeignKey("applications.application_number"), unique=True)
    missing_documents: Mapped[str] = mapped_column(Text, nullable=True)
    prev_university_and_degree: Mapped[str] = mapped_column(String(255), nullable=True)
    correct_previous_degree: Mapped[bool] = mapped_column(Boolean, nullable=True)
    degree_completed: Mapped[bool] = mapped_column(Boolean, nullable=True)
    has_min_viable_marks: Mapped[bool] = mapped_column(Boolean, nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)

    application: Mapped["Application"] = relationship(back_populates="external_applicant_data")