from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.deps import Base

class User(Base):
    __tablename__="users"
    employee_id: Mapped[str] = mapped_column(String(7), primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(255), nullable=True) # staff waiting on approval will have null roles
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc))
    approved_by: Mapped[str] = mapped_column(ForeignKey("users.employee_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

