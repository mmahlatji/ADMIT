from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.deps import Base

class User(Base):
    __tablename__="users"
    employee_id: Mapped[str] = mapped_column(String(7), primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    cell_phone: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    # role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id"), nullable=True) # staff waiting on approval will have null roles