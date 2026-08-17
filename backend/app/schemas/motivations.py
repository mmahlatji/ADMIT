"""Pydantic schemas for motivations.

MotivationCreate -> fields the client supplies.
MotivationResponse -> scalar fields from the DB row.
"""

from pydantic import BaseModel, ConfigDict


class MotivationCreate(BaseModel):
    campus_id: str
    last_name: str
    first_name: str
    motivation: str


class MotivationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    campus_id: str
    last_name: str
    first_name: str
    motivation: str
