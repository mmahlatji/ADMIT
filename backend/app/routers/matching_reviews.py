import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.matching_reviews import MatchStatus
from app.models.users import RoleEnum, User
from app.schemas.matching_reviews import MatchingReviewResponse, ResolveReviewRequest
from app.services import matching_reviews as reviews_service

router = APIRouter(prefix="/matching_reviews", tags=["matching_reviews"])


@router.get("", response_model=list[MatchingReviewResponse])
def list_reviews(
    status: MatchStatus | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(RoleEnum.convenor, RoleEnum.admin)),
):
    return reviews_service.list_reviews(db, status=status, skip=skip, limit=limit)


@router.post("/{match_id}/resolve", response_model=MatchingReviewResponse)
def resolve_review(
    match_id: uuid.UUID,
    body: ResolveReviewRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.convenor, RoleEnum.admin)),
):
    review = reviews_service.get_review_by_id(db, match_id)
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Matching review not found")
    try:
        return reviews_service.resolve_review(db, actor, review, body.resolution, body.reason)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
