from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class JoinSpec(BaseModel):
    """One entry in ``QuerySpec.joins``: a target table plus an optional ON clause."""

    model_config = ConfigDict(extra="forbid")

    table: str
    on: str | None = None


class FilterSpec(BaseModel):
    """One ``filters`` entry: column reference, operator, and the value to compare."""

    model_config = ConfigDict(extra="forbid")

    table: str | None = None
    field: str
    op: Literal["eq", "neq", "gt", "gte", "lt", "lte", "in", "like"]
    value: Any


class SelectItemSpec(BaseModel):
    """One ``select`` entry: a plain column or an aggregate over a column."""

    model_config = ConfigDict(extra="forbid")

    table: str | None = None
    field: str | None = None
    func: Literal["count", "sum", "avg", "min", "max"] | None = None
    distinct: bool = False
    alias: str | None = None


class OrderBySpec(BaseModel):
    """One ``order_by`` entry: a field (or select alias) and a direction."""

    model_config = ConfigDict(extra="forbid")

    field: str
    direction: Literal["asc", "desc"] = "asc"


class QuerySpec(BaseModel):
    """The query object the LLM emits, validated before execution."""

    model_config = ConfigDict(extra="forbid")

    base_table: str
    action: Literal["count", "select"] = "select"
    joins: list[JoinSpec] = []
    filters: list[FilterSpec] = []
    select: list[SelectItemSpec] = []
    group_by: list[str] = []
    order_by: list[OrderBySpec] = []
    distinct_rows: bool = False  # select-only: apply SELECT DISTINCT
    limit: int | None = Field(ge=0, default=None)
    offset: int | None = Field(ge=0, default=None)
    table: str | None = None  # count-only
    field: str | None = None  # count-only
    distinct: bool = False  # count-only: count(DISTINCT field)