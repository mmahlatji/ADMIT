"""Natural-language query service: schema description + saved-query orchestration.

The client sends a ``prompt``, the LLM reasons over the live schema and emits a
JSON query contract, and ``executor.py`` runs it. Successful queries are
persisted so the user can revisit them and page through the results with plain
offset/limit pagination (replaying the stored spec — no second LLM call).

The end-to-end flow is:

    prompt -> LLM emits query JSON -> execute_query -> rows -> persist SavedQuery

describe_schema builds the database description the LLM reasons over. The LLM
call is async (the slow, blocking part); the DB execution is plain sync and cheap.
"""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.llm.client import LLMClient, get_llm_client
from app.models.base import Base
from app.models.saved_queries import SavedQuery
from app.models.users import RoleEnum, User
from app.queries import saved_queries
from app.queries.nl_query import execute_query

_COMMITEE_ALLOWED_TABLES = {
    "applicants", "applications", "external_applicants_data",
    "departments", "applicant_marks", "courses", "academic_plans",
    "motivations",
}

DEFAULT_LIMIT = 100


class SavedQueryNotFoundError(Exception):
    """The requested saved query doesn't exist or doesn't belong to the actor."""


def allowed_tables_for_role(role: RoleEnum) -> set[str] | None:
    """Tables a user of this role may query; ``None`` means unrestricted."""
    if role in {RoleEnum.convenor, RoleEnum.admin}:
        return None
    return set(_COMMITEE_ALLOWED_TABLES)


def _column_info(column: Any) -> dict[str, Any]:
    """Describe one column: its SQL type and, for enums, the allowed values."""
    info: dict[str, Any] = {"type": type(column.type).__name__}
    enum_cls = getattr(column.type, "enum_class", None)
    if enum_cls is not None:
        info["values"] = [member.value for member in enum_cls]
    return info


def describe_schema(role: RoleEnum) -> dict[str, Any]:
    """
    Describe every table in the schema, for injection into the LLM prompt.

    returns: A dict of the names of the tables defined as well as additional info about the table, 
    ensuring that the llm will always have up to date knowledge of existing tables 
    """
    tables: dict[str, Any] = {}
    allowed = allowed_tables_for_role(role)
    for name in sorted(Base.metadata.tables):
        if allowed is not None and name not in allowed:
            continue
        table = Base.metadata.tables[name]
        tables[name] = {
            "columns": {column.name: _column_info(column) for column in table.columns},
            "primary_key": [column.name for column in table.primary_key.columns],
            "foreign_keys": [
                {
                    "column": fk.parent.name,
                    "references": f"{fk.column.table.name}.{fk.column.name}",
                }
                for fk in table.foreign_keys
            ],
        }
    return {"tables": tables}


async def ask(
    prompt: str, db: Session, actor: User, llm: LLMClient | None = None
) -> dict[str, Any]:
    """Answer a new question, persist it on success, and return its first page."""
    client = llm or get_llm_client()
    spec = await client.parse_intent(prompt, describe_schema(actor.role))

    title = _extract_title(spec, prompt)
    result = _run_page(spec, 0, DEFAULT_LIMIT, db, allowed_tables_for_role(actor.role))

    saved = saved_queries.create_saved_query(db, actor.user_id, prompt, title, spec)
    return {"query_id": saved.query_id, "rows": result, "title": title}


def get_page(
    query_id: uuid.UUID, skip: int, limit: int, db: Session, actor: User
) -> Any:
    """Return the page at ``skip`` of a saved query, re-running it live."""
    saved = _get_owned(db, actor, query_id)
    return _run_page(saved.spec, skip, limit, db, allowed_tables_for_role(actor.role))


def list_queries(db: Session, actor: User) -> list[SavedQuery]:
    """List the actor's saved queries, newest first."""
    return saved_queries.list_saved_queries(db, actor.user_id)


def delete_query(db: Session, actor: User, query_id: uuid.UUID) -> None:
    """Delete one of the actor's saved queries."""
    saved = _get_owned(db, actor, query_id)
    saved_queries.delete_saved_query(db, saved)


def _get_owned(db: Session, actor: User, query_id: uuid.UUID) -> SavedQuery:
    """Fetch a saved query, raising if it isn't the actor's."""
    saved = saved_queries.get_saved_query(db, actor.user_id, query_id)
    if saved is None:
        raise SavedQueryNotFoundError(f"Saved query {query_id} not found")
    return saved


def _run_page(
    spec: dict[str, Any], offset: int, limit: int, db: Session, allowed_tables: set[str] | None = None
) -> Any:
    """Execute ``spec`` with the client's offset/limit; counts ignore both."""
    if spec.get("action") == "count":
        return execute_query(spec, db, allowed_tables=allowed_tables)

    paged = dict(spec)
    paged["offset"] = offset
    paged["limit"] = limit
    return execute_query(paged, db, allowed_tables=allowed_tables)


def _extract_title(spec: dict[str, Any], prompt: str) -> str:
    """Pull the LLM's ``title`` out of the spec, falling back to the prompt.

    ``title`` is metadata, not part of the executable query, so it is popped
    before the spec is executed (``QuerySpec`` forbids extra keys).
    """
    title = str(spec.pop("title", "") or "").strip()
    if title:
        return title
    fallback = prompt.strip()
    if len(fallback) > 80:
        fallback = fallback[:77] + "..."
    return fallback
