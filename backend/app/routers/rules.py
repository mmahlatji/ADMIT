from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.users import RoleEnum, User
from app.schemas.rules import (
    RuleCreate,
    RulePreviewRequest,
    RulePreviewResponse,
    RuleResponse,
    RuleStatus,
)
from app.services import rules as rules_service
from app.services.engine.tools import RuleConflict, VariableError
from uuid import UUID

router = APIRouter(prefix="/rules", tags=["rules"])

MAX_PAGE_SIZE = 500

# Rules decide who gets in, so writing one is convenor/admin only. Committee
# members can read what is in force but not change it.
WRITE_ROLES = [RoleEnum.convenor, RoleEnum.admin]
READ_ROLES = [RoleEnum.convenor, RoleEnum.committee, RoleEnum.admin]


@router.get("", response_model=list[RuleResponse])
def list_rules(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _: User = Depends(require_role(*READ_ROLES)),
):
    """Every rule that has been saved, newest first."""
    return rules_service.list_rules(db, skip=skip, limit=limit)


@router.post("/preview", response_model=RulePreviewResponse)
def preview_rule(
    body: RulePreviewRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(*WRITE_ROLES)),
):
    """Show what a proposed rule would do to this intake, without saving it.

    This is the point of the rule engine: a convenor sees how many applicants
    the rule would admit, and how that differs from the rules already in force,
    before committing to it.
    """
    try:
        return rules_service.preview_rule(
            db, body.institution, body.intake_year, body.expression, body.rule_action
        )
    except VariableError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except RuleConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except rules_service.NoMarksError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    body: RuleCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(*WRITE_ROLES)),
):
    """Save a rule as active for this intake."""
    try:
        return rules_service.save_rule(
            db,
            body.institution,
            body.intake_year,
            body.expression,
            body.rule_action,
            actor.employee_id,
        )
    except VariableError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except RuleConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except rules_service.NoMarksError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.post("/apply", status_code=status.HTTP_200_OK)
def apply_rules(
    intake_year: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(*WRITE_ROLES)),
):
    """Recompute admission statuses for the given intake using current active rules."""
    try:
        rules_service.apply_rules(db, intake_year)

        return {"status": "applied"}
    except rules_service.NoRuleException as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/{rule_id}/status", status_code=status.HTTP_200_OK)
def update_status(
    rule_id: UUID,
    new_status: RuleStatus,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(*WRITE_ROLES)),
):

    try:
        return rules_service.update_rule_status(db, rule_id, new_status)
    except rules_service.NoRuleException as exec:
        raise HTTPException(status_code=404, detail=str(exec))
    except rules_service.InvalidRuleTransitionError as exec:
        raise HTTPException(status_code=400, detail=str(exec))
