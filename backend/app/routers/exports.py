from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.applications import ApplicationStatus
from app.models.users import RoleEnum, User
from app.services.exports import (
    MissingApplicantDataError,
    NoDecisionsFoundError,
    generate_decisions_by_year,
)

router = APIRouter(prefix="/exports", tags=["exports"])


def build_decisions_filename(
    year: int,
    today: date | None = None,
    statuses: list[ApplicationStatus] | None = None,
) -> str:
    """
    Builds the export filename. Recent years (within the last 12 months)
    get today's date appended, since that period's data can still change;
    older years are stable, so just the year is enough.

    A single named stage titles the file after that stage, so a folder of
    exports says what each one is rather than four files all called Decisions.
    """
    today = today or datetime.now(UTC).date()
    year_start = date(year, 1, 1)
    is_recent = (today - year_start).days < 365

    label = statuses[0].value if statuses and len(statuses) == 1 else "Decisions"

    if is_recent:
        return f"{label} - {today.isoformat()}.xlsx"
    return f"{label} - {year}.xlsx"


@router.get("/decisions")
def export_decisions(
    year: int = Query(..., ge=2000, le=2100),
    status: Annotated[
        list[ApplicationStatus] | None,
        Query(description="Stages to export. Repeat for several. Omit for settled decisions."),
    ] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(RoleEnum.convenor, RoleEnum.admin)),
):
    try:
        buffer = generate_decisions_by_year(db, year, status)
        filename = build_decisions_filename(year, statuses=status)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except NoDecisionsFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except MissingApplicantDataError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
