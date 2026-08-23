import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.users import RoleEnum


class UserOut(BaseModel):
    """What a user looks like over the wire."""

    user_id: uuid.UUID
    employee_id: str | None
    first_name: str | None
    last_name: str | None
    email: str
    role: RoleEnum | None
    approved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleAssignment(BaseModel):
    """Request body for granting (a role) or revoking (null) a user's access."""

    role: RoleEnum | None
