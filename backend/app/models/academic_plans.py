import uuid
from enum import Enum

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AcademicPlanType(str, Enum): # need this in order to check if an appliction is incorrect
    INTERNAL = "Internal"
    EXTERNAL = "External"

class AcademicPlan(Base):
    __tablename__="academic_plans"
    academic_plan_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    department_code: Mapped[str] = mapped_column(ForeignKey("department_codes.department_code"), nullable=False)
    academic_plan: Mapped[str] = mapped_column(String(10), nullable=False, unique=True, index=True)
    plan_type: Mapped[AcademicPlanType] = mapped_column(SQLEnum(AcademicPlanType, name="academic_plan_type"), nullable=False)