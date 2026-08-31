from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.users import RoleEnum, User
from app.schemas.votes import VoteCreateRequest, VoteResponse
from app.services import votes as votes_service

router = APIRouter(prefix="/votes", tags=["votes"])

ALLOWED_ROLES = [RoleEnum.convenor, RoleEnum.committee, RoleEnum.admin]


@router.get("", response_model=list[VoteResponse])
def list_votes(
    application_number: str | None = None,
    campus_id: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(*ALLOWED_ROLES)),
):
    return votes_service.list_votes(
        db, application_number=application_number, campus_id=campus_id, skip=skip, limit=limit
    )


@router.post("", response_model=VoteResponse, status_code=status.HTTP_201_CREATED)
def create_vote(
    body: VoteCreateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(*ALLOWED_ROLES)),
):
    try:
        return votes_service.create_vote(db, actor, body.application_number, body.vote)
    except votes_service.ApplicationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found") from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc