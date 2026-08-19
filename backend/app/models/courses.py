import uuid
from sqlalchemy import ForeignKey, Integer, String, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Course(Base):
    __tablename__="courses"
    course_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    academic_program_code: Mapped[str] = mapped_column(ForeignKey("academic_programs.academic_program_code"), nullable=False, index=True)
    course_code: Mapped[str] = mapped_column(String(8), nullable=False, unique=True, index=True)
    course_name: Mapped[str] = mapped_column(String(255), nullable=True)