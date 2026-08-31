import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Document(Base):
    __tablename__="documents"
    document_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    import_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("import_runs.import_run_id"), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())