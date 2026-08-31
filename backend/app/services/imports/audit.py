"""Writes an audit trail of what an import actually changed."""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.system_logs import ChangeSource
from app.queries.system_logs import create_system_log


def _json_safe(value: Any) -> Any:
    """Coerce a value that JSON can't natively encode (date/datetime) into one
    it can. Our own domain enums are all (str, Enum) mixins so they already
    serialize as plain strings and don't need any help here.
    """
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def record_change(
    db: Session,
    entity_name: str,
    entity_id: uuid.UUID,
    changed_by: str,
    import_run_id: uuid.UUID,
    old_data: dict[str, Any],
    new_data: dict[str, Any],
) -> None:
    """Log a field-level change made by an import, if anything actually changed.

    Diffs old_data/new_data key by key and only logs the keys that differ - a
    true no-op re-import (identical values) writes nothing here, which is what
    keeps a repeat import from generating audit noise.
    """
    old_data = {key: _json_safe(value) for key, value in old_data.items()}
    new_data = {key: _json_safe(value) for key, value in new_data.items()}
    changed_keys = {key for key in new_data if old_data.get(key) != new_data.get(key)}
    if not changed_keys:
        return

    create_system_log(
        db,
        entity_name=entity_name,
        entity_id=entity_id,
        changed_by=changed_by,
        reason=ChangeSource.IMPORT,
        old_data={key: old_data.get(key) for key in changed_keys},
        new_data={key: new_data[key] for key in changed_keys},
        import_run_id=import_run_id,
    )
