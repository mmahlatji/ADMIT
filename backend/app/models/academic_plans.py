import uuid

from sqlalchemy import UUID, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AcademicPlan(Base):
    __tablename__="academic_plans"
    academic_plan_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    academic_plan: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    academic_program_code: Mapped[str] = mapped_column(String(10), nullable=False)