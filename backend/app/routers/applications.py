import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.applications import ApplicationStatus
from app.models.users import RoleEnum, User
from app.schemas.applications import ApplicationResponse, ApplicationStatusTransition
from app.services import applications as applications_service

router = APIRouter(prefix="/applications", tags=["applications"])

MAX_PAGE_SIZE = 500

ALLOWED_ROLES = [RoleEnum.convenor, RoleEnum.committee, RoleEnum.admin]


@router.get("", response_model=list[ApplicationResponse])
def list_applications(
    campus_id: str | None = None,
    application_status: ApplicationStatus | None = None,
    application_number: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _: User = Depends(require_role(*ALLOWED_ROLES)),
):
    return applications_service.list_applications(
        db,
        campus_id=campus_id,
        application_status=application_status,
        application_number=application_number,
        skip=skip,
        limit=limit,
    )


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(*ALLOWED_ROLES)),
):
    application = applications_service.get_application_by_id(db, application_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    return application


@router.post("/{application_id}/status", response_model=ApplicationResponse)
def transition_status(
    application_id: uuid.UUID,
    body: ApplicationStatusTransition,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(*ALLOWED_ROLES)),
):
    application = applications_service.get_application_by_id(db, application_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    try:
        return applications_service.transition_status(db, actor, application, body.status, body.reason)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
