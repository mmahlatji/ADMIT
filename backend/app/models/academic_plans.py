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
    # was department_codes.department_code, that table got renamed to departments and this FK never got updated
    department_code: Mapped[str] = mapped_column(ForeignKey("departments.department_code"), nullable=False)
    academic_plan: Mapped[str] = mapped_column(String(10), nullable=False, unique=True, index=True)
    # values_callable like the other seven enums f65e730dde7d renamed: that
    # migration relabelled this type from member names to values on the
    # premise it had gained values_callable too, and it had not. The database
    # has said Internal/External ever since while the model still asked for
    # INTERNAL/EXTERNAL, so every read of a plan raised LookupError and every
    # ASR row was rejected before it could be reconciled.
    plan_type: Mapped[AcademicPlanType] = mapped_column(
        SQLEnum(
            AcademicPlanType,
            name="academic_plan_type",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )