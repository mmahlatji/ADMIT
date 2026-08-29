import uuid

from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    """Fields the client supplies to create a department."""

    department_code: str
    department_name: str | None = None


class DepartmentUpdate(BaseModel):
    """Partial update for a department, only set fields are applied."""

    department_code: str | None = None
    department_name: str | None = None


class DepartmentResponse(DepartmentCreate):
    """What a department looks like over the wire."""

    department_id: uuid.UUID

    model_config = {"from_attributes": True}
