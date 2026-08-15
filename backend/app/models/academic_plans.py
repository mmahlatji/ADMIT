from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.deps import Base


class AcademicPlan(Base):
    __tablename__="academic_plans"
    academic_plan: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    academic_program_code: Mapped[str] = mapped_column(ForeignKey("academic_program.academic_program_code"), nullable=False)