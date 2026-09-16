import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StudentDocument(Base):
    __tablename__="student_documents"
    __table_args__ = (
        # Per applicant, not global: two applicants may legitimately upload
        # byte-identical files, e.g. the same blank form.
        UniqueConstraint(
            "applicant_id", "sha256_hash", name="uq_student_document_applicant_hash"
        ),
    )
    document_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    applicant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applicants.applicant_id"), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())