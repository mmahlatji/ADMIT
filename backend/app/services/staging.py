import uuid

from sqlalchemy.orm import Session

from app.models.staging import Staging
from app.queries import staging as staging_queries


def get_batched_pending_rows(db: Session, import_run_id: uuid.UUID, batch_size: int) -> list[Staging]:
    return staging_queries.get_batched_pending_rows_by_import_id(db, import_run_id, batch_size)
