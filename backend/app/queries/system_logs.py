import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.system_logs import ChangeSource, SystemLog


def get_system_log_by_id(db: Session, log_id: uuid.UUID) -> SystemLog | None:
    """Look up a system log entry by its id. Returns None if it doesn't exist yet."""
    return db.execute(select(SystemLog).where(SystemLog.log_id == log_id)).scalar_one_or_none()


def get_system_logs(db: Session, skip: int = 0, limit: int = 100) -> list[SystemLog]:
    """List system log entries, paginated."""
    return list(db.execute(select(SystemLog).offset(skip).order_by(SystemLog.changed_at.desc()).limit(limit)).scalars())


def create_system_log(
    db: Session,
    entity_name: str,
    entity_id: uuid.UUID,
    changed_by: str,
    reason: ChangeSource,
    old_data: dict[str, Any] | None = None,
    new_data: dict[str, Any] | None = None,
    import_run_id: uuid.UUID | None = None,
) -> SystemLog:
    """Insert a new system log row."""
    log = SystemLog(
        log_id=uuid.uuid4(),
        entity_name=entity_name,
        entity_id=entity_id,
        changed_by=changed_by,
        old_data=old_data,
        new_data=new_data,
        reason=reason,
        import_run_id=import_run_id,
    )
    db.add(log)
    db.flush()
    db.refresh(log)
    return log


def update_system_log(
    db: Session,
    log: SystemLog,
    entity_name: str | None = None,
    entity_id: uuid.UUID | None = None,
    changed_by: str | None = None,
    old_data: dict[str, Any] | None = None,
    new_data: dict[str, Any] | None = None,
    reason: ChangeSource | None = None,
    import_run_id: uuid.UUID | None = None,
) -> SystemLog:
    """Partially update a system log row, only sets fields explicitly passed."""
    fields = {
        "entity_name": entity_name,
        "entity_id": entity_id,
        "changed_by": changed_by,
        "old_data": old_data,
        "new_data": new_data,
        "reason": reason,
        "import_run_id": import_run_id,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(log, field, value)
    db.flush()
    db.refresh(log)
    return log



