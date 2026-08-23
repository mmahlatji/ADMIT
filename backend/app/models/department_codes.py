import uuid

from sqlalchemy import UUID, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class DepartmentCode(Base):
    __tablename__="department_codes"
    department_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    department_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False, index=True) 
    department_name: Mapped[str] = mapped_column(String(255), nullable=True) # The name of the academic program