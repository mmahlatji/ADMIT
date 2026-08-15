from datetime import date
from sqlalchemy import String, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.deps import Base


class Applicant(Base):
    __tablename__="applicants"

    campus_id: Mapped[str] = mapped_column(String(9), primary_key=True, index=True)
    employee_id: Mapped[str] = mapped_column(String(7), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False,  unique=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=False)
    sex: Mapped[str] = mapped_column(String(255), nullable=False) # I dont know if I should use an enum{Male, Female, Other} or what ?
    cell_phone: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    home_phone: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    population_group: Mapped[str] = mapped_column(String(15), nullable=False)
    id_number: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    citizenship_residency: Mapped[str] = mapped_column(String(255), nullable=False)
    non_sa_citizenship: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True) # index if we filter based on citizenship
    applied_for_academic_program: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # document_path






