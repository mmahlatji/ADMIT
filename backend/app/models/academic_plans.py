import uuid

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AcademicPlan(Base):
    __tablename__="academic_plans"
    academic_plan_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    academic_plan: Mapped[str] = mapped_column(String(5), nullable=False, unique=True, index=True)
    department_code: Mapped[str] = mapped_column(ForeignKey("department_codes.department_code"), nullable=False)