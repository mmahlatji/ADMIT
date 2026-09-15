import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.rules import Institution, RuleAction, RuleStatus


class RulePreviewRequest(BaseModel):
    """A rule a convenor is considering, not yet saved."""

    institution: Institution
    intake_year: int
    expression: str
    rule_action: RuleAction


class RuleCreate(RulePreviewRequest):
    """A rule the convenor has previewed and decided to keep."""


class RulePreviewResponse(BaseModel):
    """What a proposed rule would do to the current intake.

    before/pass_rate_before are absent when this is the first rule for the
    intake: there is no prior state to compare against.
    """

    first_rule: bool
    after: int
    # applicants with no mark for a course the rule uses: counted as not
    # admitted, reported so the headline number can be read honestly
    not_evaluable: int = 0
    pass_rate_after: float
    before: int | None = None
    change: int | None = None
    pct_change: float | None = None
    pass_rate_before: float | None = None


class RuleResponse(BaseModel):
    """A saved rule."""

    model_config = ConfigDict(from_attributes=True)

    rule_id: uuid.UUID
    institution: Institution
    intake_year: int
    version: int
    rule: str
    status: RuleStatus
    rule_action: RuleAction
    created_by: str
    created_at: datetime
