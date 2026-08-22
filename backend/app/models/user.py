import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class RoleEnum(str, enum.Enum):
    """The three roles a user can hold. Null role means not approved yet."""

    admin = "admin"
    convenor = "convenor"
    committee = "committee"


class User(Base):
    """A staff account. Created on first login, starts with role=null until approved."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    employee_id: Mapped[str | None] = mapped_column(String(7), unique=True, index=True)
    # first and last name are nullable: a bare Supabase JWT doesn't carry a name, only sub/email. Filled in from signup metadata if the frontend sends it, left null otherwise.
    # we can set nullable to false we just have to make sure the frontend sends the name in the signup metadata, which it currently isn't planned to do. so we can discuss this further ig
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[RoleEnum | None] = mapped_column(Enum(RoleEnum, name="role"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[str | None] = mapped_column(ForeignKey("users.employee_id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False 
    )

    # notes/votes relationships will be added by Molly here, doesn't exist yet on mine so might break my tests
