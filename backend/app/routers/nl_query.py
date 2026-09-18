"""HTTP layer for natural-language queries and their saved-query history."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.llm.exceptions import LLMResponseError, LLMUnavailableError
from app.models.users import RoleEnum, User
from app.schemas.nl_query import QueryAskResponse, QueryRequest, QueryResult, SavedQueryMeta
from app.services import nl_query as nl_query_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/query", tags=["nl_query"])

_ALLOWED_ROLES = [RoleEnum.convenor, RoleEnum.committee, RoleEnum.admin]

# A saved query replays against the live database, so an unbounded limit lets
# one request pull the whole table into memory.
MAX_PAGE_SIZE = 500


@router.post("", response_model=QueryAskResponse)
async def ask(
    body: QueryRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(*_ALLOWED_ROLES)),
) -> QueryAskResponse:
    try:
        return await nl_query_service.ask(body.prompt, db, actor)
    except LLMUnavailableError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except LLMResponseError as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"LLM produced an invalid query: {exc}"
        ) from exc
    # The executor guards the known PostgreSQL rules, but an unanticipated SQL
    # error must still fail cleanly. Logged rather than returned: a
    # SQLAlchemyError stringifies to the whole statement and its parameters,
    # which would hand back the schema the rest of this module takes care not
    # to name, and hand a committee member the tables their role excludes.
    except SQLAlchemyError as exc:
        logger.exception("nl_query ask failed while executing the generated query")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "The query could not be run against the database",
        ) from exc


@router.get("", response_model=list[SavedQueryMeta])
def list_saved(
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(*_ALLOWED_ROLES)),
) -> list[SavedQueryMeta]:
    return nl_query_service.list_queries(db, actor)


@router.get("/{query_id}", response_model=QueryResult)
def page(
    query_id: uuid.UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(*_ALLOWED_ROLES)),
) -> QueryResult:
    try:
        return nl_query_service.get_page(query_id, skip, limit, db, actor)
    except nl_query_service.SavedQueryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Saved query produced an invalid query: {exc}"
        ) from exc
    # Same as ``ask``: a saved query replays live, so it can hit the same
    # unanticipated SQL errors, and the same reason not to echo them back.
    except SQLAlchemyError as exc:
        logger.exception("nl_query page failed while replaying saved query %s", query_id)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "The saved query could not be run against the database",
        ) from exc


@router.delete("/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved(
    query_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(*_ALLOWED_ROLES)),
) -> None:
    try:
        nl_query_service.delete_query(db, actor, query_id)
    except nl_query_service.SavedQueryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
