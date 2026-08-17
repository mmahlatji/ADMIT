from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.deps import Base


class AcademicProgram(Base):
    __tablename__="academic_programs"
    academic_program_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    academic_program_code: Mapped[str] = mapped_column(String(6), unique=True, nullable=False, index=True) # if these are fixed we could just make it an enum
    academic_program: Mapped[str] = mapped_column(String(255), nullable=True) # The name of the academic program