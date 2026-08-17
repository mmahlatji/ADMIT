from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.deps import Base


class AcademicPlan(Base):
    __tablename__="academic_plans"
    academic_plan_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    academic_plan: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    academic_program_code: Mapped[str] = mapped_column(ForeignKey("academic_program.academic_program_code"), nullable=False)