from datetime import date, datetime
from sqlalchemy import Float, ForeignKey, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.deps import Base

class Motivation(Base):
    __tablename__="motivations"
    campus_id: Mapped[str] = mapped_column(ForeignKey("applicants.campus_id"), primary_key=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    motivation: Mapped[str] = mapped_column(Text, nullable=False)
