from datetime import date, datetime
from sqlalchemy import Float, ForeignKey, DateTime, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.deps import Base


class Course(Base):
    __tablename__="courses"
    course_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    academic_program_code: Mapped[str] = mapped_column(ForeignKey("academic_program.academic_program_code"), nullable=False, index=True)
    course_code: Mapped[str] = mapped_column(String(8), nullable=False, unique=True, index=True)
    course_name: Mapped[str] = mapped_column(String(255), nullable=True)