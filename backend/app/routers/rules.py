from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.users import RoleEnum, User
from app.schemas.rules import (
    RuleCreate,
    RulePreviewRequest,
    RulePreviewResponse,
    RuleResponse,
)
from app.services import rules as rules_service
from app.services.rule_engine import RuleConflict, VariableError

router = APIRouter(prefix="/rules", tags=["rules"])

# Rules decide who gets in, so writing one is convenor/admin only. Committee
# members can read what is in force but not change it.
WRITE_ROLES = [RoleEnum.convenor, RoleEnum.admin]
READ_ROLES = [RoleEnum.convenor, RoleEnum.committee, RoleEnum.admin]


@router.get("", response_model=list[RuleResponse])
def list_rules(
    skip: int = 0,
    limit: int = 100,
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
            db, body.institution, body.intake_year, body.expression
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
            db, body.institution, body.intake_year, body.expression, actor.employee_id
        )
    except VariableError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except RuleConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except rules_service.NoMarksError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
