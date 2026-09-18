import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Column
from sqlalchemy import Enum as SQLEnum


def _coerce_enum(enum_cls: type, value: Any) -> Any:
    """Match ``value`` to a member of ``enum_cls`` (by value, or via str ctor)."""
    if isinstance(value, enum_cls):
        return value
    for member in enum_cls:
        if member.value == value:
            return member
    try:
        return enum_cls(value)
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid value") from exc


def coerce_value(column: Column, value: Any) -> Any:
    """Convert a JSON value into the Python type ``column`` expects.

    JSON only carries strings/numbers/bools/lists, so values for UUID, date,
    datetime, numeric and enum columns arrive as strings and would otherwise
    fail. Coerce them here and raise a clear ``ValueError`` on bad input. 
    Lists (e.g. for ``in``) are coerced element-wise.
    """
    if value is None:
        return value
    if isinstance(value, list):
        return [coerce_value(column, item) for item in value]

    column_type = column.type
    if isinstance(column_type, SQLEnum):
        return _coerce_enum(column_type.enum_class, value)

    target = column_type.python_type
    if isinstance(value, target):
        return value

    try:
        if target is uuid.UUID:
            return uuid.UUID(str(value))
        if target is datetime:
            return datetime.fromisoformat(value)
        if target is date:
            return date.fromisoformat(value)
        if target is int:
            return int(value)
        if target is float:
            return float(value)
        if target is bool:
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in ("true", "1", "yes"):
                    return True
                if lowered in ("false", "0", "no"):
                    return False
            raise ValueError
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"Invalid {type(column_type).__name__} value") from exc

    return value

def to_jsonable(value: Any) -> Any:
    """Convert a DB value into something JSON-serializable."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    return value