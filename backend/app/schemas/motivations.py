"""Pydantic schemas for motivations.

MotivationCreate -> fields the client supplies.
MotivationResponse -> scalar fields from the DB row.
"""

from pydantic import BaseModel, ConfigDict, Field


class MotivationCreate(BaseModel):
    campus_id: str = Field(min_length=1, max_length=9)
    last_name: str = Field(min_length=1)
    first_name: str = Field(min_length=1)
    motivation: str = Field(min_length=1)


class MotivationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    campus_id: str
    last_name: str
    first_name: str
    motivation: str
