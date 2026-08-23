import uuid

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Course(Base):
    __tablename__="courses"
    course_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    department_code: Mapped[str] = mapped_column(ForeignKey("department_codes.department_code"), nullable=False, index=True)
    course_code: Mapped[str] = mapped_column(String(8), nullable=False, unique=True, index=True)
    course_name: Mapped[str] = mapped_column(String(255), nullable=True)