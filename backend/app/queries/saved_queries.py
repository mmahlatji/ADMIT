"""Data access for persisted natural-language queries."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.saved_queries import SavedQuery


def create_saved_query(
    db: Session, user_id: uuid.UUID, prompt: str, title: str | None, spec: dict[str, Any]
) -> SavedQuery:
    """Persist a successfully executed query so the user can revisit it."""
    saved = SavedQuery(
        query_id=uuid.uuid4(), user_id=user_id, prompt=prompt, title=title, spec=spec
    )
    db.add(saved)
    db.flush()
    return saved


def get_saved_query(db: Session, user_id: uuid.UUID, query_id: uuid.UUID) -> SavedQuery | None:
    """Look up one of the user's saved queries, or None if not found / not theirs."""
    return db.execute(
        select(SavedQuery).where(
            SavedQuery.query_id == query_id, SavedQuery.user_id == user_id
        )
    ).scalar_one_or_none()


def list_saved_queries(db: Session, user_id: uuid.UUID) -> list[SavedQuery]:
    """List a user's saved queries, newest first."""
    return list(
        db.execute(
            select(SavedQuery)
            .where(SavedQuery.user_id == user_id)
            .order_by(SavedQuery.created_at.desc())
        ).scalars()
    )


def delete_saved_query(db: Session, saved: SavedQuery) -> None:
    """Delete a saved query row."""
    db.delete(saved)
    db.flush()
