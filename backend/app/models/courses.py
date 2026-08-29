import uuid

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Course(Base):
    __tablename__="courses"
    course_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    # was department_codes.department_code, that table got renamed to departments and this FK never got updated
    department_code: Mapped[str] = mapped_column(ForeignKey("departments.department_code"), nullable=False, index=True)
    course_code: Mapped[str] = mapped_column(String(15), nullable=False, unique=True, index=True)
    course_name: Mapped[str] = mapped_column(String(255), nullable=True)