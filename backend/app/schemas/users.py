"""Pydantic schemas for users.

UserCreate -> fields the client supplies (server-generated fields omitted).
UserResponse -> scalar fields from the DB row.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    employee_id: str = Field(min_length=1, max_length=7)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: EmailStr
    role: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: str
    first_name: str
    last_name: str
    email: EmailStr
    role: str | None
    approved_at: datetime | None
    approved_by: str | None
    created_at: datetime
