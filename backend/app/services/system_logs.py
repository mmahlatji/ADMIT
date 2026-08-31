"""Service layer for writing system logs."""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.system_logs import ChangeSource, SystemLog
from app.queries import system_logs as system_log_queries


def create_log(
    db: Session,
    entity_name: str,
    entity_id: uuid.UUID,
    old_data: dict[str, Any],
    new_data: dict[str, Any],
    changed_by: str,
    reason: ChangeSource,
    import_run_id: uuid.UUID | None = None,
) -> SystemLog:
    """Record a change to an entity in the system log. Does not commit."""
    return system_log_queries.create_system_log(
        db,
        entity_name=entity_name,
        entity_id=entity_id,
        old_data=old_data,
        new_data=new_data,
        changed_by=changed_by,
        reason=reason,
        import_run_id=import_run_id,
    )


def list_logs(
    db: Session,
    entity_name: str | None = None,
    entity_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[SystemLog]:
    return system_log_queries.list_logs(db, entity_name, entity_id, skip, limit)



def get_latest_log_by_entity_and_entity_id(db: Session, entity_name: str, entity_id: uuid.UUID) -> SystemLog | None:
    return system_log_queries.get_latest_system_log_by_entity_and_entity_id(db, entity_name, entity_id)