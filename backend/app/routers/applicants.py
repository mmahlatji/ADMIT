from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.users import RoleEnum, User
from app.schemas.applicants import ApplicantDetail, ApplicantResponse
from app.services import applicants as applicants_service

router = APIRouter(prefix="/applicants", tags=["applicants"])

ALLOWED_ROLES = [RoleEnum.convenor, RoleEnum.committee, RoleEnum.admin]


@router.get("", response_model=list[ApplicantResponse])
def list_applicants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(*ALLOWED_ROLES)),
):
    return applicants_service.list_applicants(db, skip=skip, limit=limit)


@router.get("/{campus_id}", response_model=ApplicantDetail)
def get_applicant(
    campus_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(*ALLOWED_ROLES)),
):
    applicant = applicants_service.get_applicant_by_campus_id(db, campus_id)
    if applicant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Applicant not found")
    return applicant
