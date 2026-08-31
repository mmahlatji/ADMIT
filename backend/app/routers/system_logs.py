import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.users import RoleEnum, User
from app.schemas.system_logs import SystemLogResponse
from app.services import system_logs as system_logs_service

router = APIRouter(prefix="/system_logs", tags=["system_logs"])


@router.get("", response_model=list[SystemLogResponse])
def list_logs(
    entity_name: str | None = None,
    entity_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(RoleEnum.convenor, RoleEnum.admin)),
):
    return system_logs_service.list_logs(
        db, entity_name=entity_name, entity_id=entity_id, skip=skip, limit=limit
    )
