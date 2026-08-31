"""Deterministic value mappings from raw sheet vocabulary to our enum members.

Not fuzzy matching - every legal raw value is listed explicitly here. An
unrecognized value raises RowReconciliationError so the row gets flagged for a
human instead of silently dropped or coerced into the wrong thing.
"""
from datetime import date, datetime
from typing import Any

import pandas as pd

from app.models.applicants import CitizenshipResidency, SexEnum, TitleEnum
from app.models.applications import Choice, Semester
from app.services.imports.results import RowReconciliationError

# real ASR exports use FRST/SCND directly (confirmed against the source
# system's documented vocabulary); the lowercase variants cover test/sample data
CHOICE_MAP: dict[str, Choice] = {
    "FRST": Choice.FIRST,
    "first": Choice.FIRST,
    "SCND": Choice.SECOND,
    "second": Choice.SECOND,
}

SEMESTER_MAP: dict[str, Semester] = {
    "1st Semester": Semester.FIRST,
    "first": Semester.FIRST,
    "2nd Semester": Semester.SECOND,
    "second": Semester.SECOND,
}

SEX_MAP: dict[str, SexEnum] = {
    "M": SexEnum.MALE,
    "male": SexEnum.MALE,
    "F": SexEnum.FEMALE,
    "female": SexEnum.FEMALE,
}

CITIZENSHIP_MAP: dict[str, CitizenshipResidency] = {
    "SA Citizen": CitizenshipResidency.SA_CITIZEN,
    "International": CitizenshipResidency.INTERNATIONAL,
    "Permanent Resident": CitizenshipResidency.PERMANENT_RESIDENT,
}

TITLE_MAP: dict[str, TitleEnum] = {
    "mr": TitleEnum.MR,
    "Mr": TitleEnum.MR,
    "ms": TitleEnum.MS,
    "Ms": TitleEnum.MS,
    "Miss": TitleEnum.MISS,
    "miss": TitleEnum.MISS
}


def coerce(value: Any, mapping: dict[str, Any], field_name: str) -> Any:
    """Map a raw sheet value onto one of our enum members.

    Tries an exact match first, then a case-insensitive/stripped match, since
    the source system spells the same thing inconsistently across sheets.
    A blank value passes through as None (nullability is the column's call,
    not this function's).
    """
    if value is None or value.strip() == "":
        return None
    if value in mapping:
        return mapping[value]

    normalized = str(value).strip().lower()
    for raw, member in mapping.items():
        if raw.strip().lower() == normalized:
            return member

    raise RowReconciliationError(f"unrecognized value {value!r} for {field_name}")



def parse_date(value) -> date | None:
    """Coerce a sheet cell into a date. Handles None, ISO strings, date,
    datetime, and pd.Timestamp (a datetime subclass, so no pandas import)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    return date.fromisoformat(text)

def parse_int(value: str | None) -> int | None:
    if value is None or not str(value).strip():
        return None
    return int(str(value).strip())

def clean_cell(value):
    """Normalize one pandas cell for reconciliation: NaN/NaT and whitespace-only
    strings become None. Blank cells are a sheet artifact, not data - and a
    whitespace string in a UNIQUE column (e.g. applicants.cell_phone) would
    collide across rows, whereas NULL does not."""
    if value is None:
        return None
    if pd.isna(value):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value