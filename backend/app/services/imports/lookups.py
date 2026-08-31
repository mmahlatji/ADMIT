"""Natural-key lookups for one import run, answered from a bulk prefetch.

The reconcilers work a row at a time and each row asks "does this applicant
exist, does this application exist". Done literally that is two queries per
row, which is most of an import's cost against a hosted database.

The orchestrator primes this once per run with every key the sheet mentions,
in one query per entity. After that a lookup is a dict hit, and a miss is
authoritative: the prefetch covered every key the sheet can ask about, so
anything absent genuinely is not in the database.

Rows created mid-run are written back into the cache, so later rows in the
same sheet see earlier ones, which is what makes a sheet containing the same
applicant twice behave the same as it did before.

When nothing has primed the cache (a reconciler called directly, as the unit
tests do) every lookup falls through to its plain query, so behaviour is
unchanged.
"""

from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.applicant_marks import ApplicantMark
from app.models.applicants import Applicant
from app.models.applications import Application
from app.models.motivations import Motivation
from app.queries.applicant_marks import get_applicant_mark_by_campus_and_course
from app.queries.applicants import get_applicant_by_campus_id
from app.queries.applications import get_application_by_number
from app.queries.motivations import get_motivation_by_campus_id

_KEY = "_import_lookups"


def _cache(db: Session) -> dict | None:
    return db.info.get(_KEY)


def prime(
    db: Session,
    *,
    campus_ids: set[str],
    application_numbers: set[str] | None = None,
    course_codes: set[str] | None = None,
) -> None:
    """Load everything the sheet refers to, one query per entity."""
    campus_ids = {c for c in campus_ids if c}
    application_numbers = {a for a in (application_numbers or set()) if a}

    applicants = {}
    applications = {}
    marks = {}
    motivations = {}

    if campus_ids:
        for applicant in db.scalars(
            select(Applicant).where(Applicant.campus_id.in_(campus_ids))
        ):
            applicants[applicant.campus_id] = applicant
        for motivation in db.scalars(
            select(Motivation).where(Motivation.campus_id.in_(campus_ids))
        ):
            motivations[motivation.campus_id] = motivation
        if course_codes:
            for mark in db.scalars(
                select(ApplicantMark).where(
                    ApplicantMark.campus_id.in_(campus_ids),
                    ApplicantMark.course_code.in_(course_codes),
                )
            ):
                marks[(mark.campus_id, mark.course_code)] = mark

    # Applications are fetched by number AND by campus id, not just by the
    # numbers in the sheet. Duplicate detection asks for every application an
    # applicant has this cycle, which includes ones written by an earlier
    # import that this sheet never mentions. Fetching by number alone would
    # hide those and stop duplicates being detected across imports.
    if application_numbers or campus_ids:
        conditions = []
        if application_numbers:
            conditions.append(Application.application_number.in_(application_numbers))
        if campus_ids:
            conditions.append(Application.campus_id.in_(campus_ids))
        for application in db.scalars(select(Application).where(or_(*conditions))):
            applications[application.application_number] = application

    db.info[_KEY] = {
        "applicants": applicants,
        "applications": applications,
        "marks": marks,
        "motivations": motivations,
    }


def clear(db: Session) -> None:
    """Drop the cache so a later run in the same session starts clean."""
    db.info.pop(_KEY, None)


def applicant_by_campus_id(db: Session, campus_id: str) -> Applicant | None:
    cache = _cache(db)
    if cache is None:
        return get_applicant_by_campus_id(db, campus_id)
    return cache["applicants"].get(campus_id)


def application_by_number(db: Session, application_number: str) -> Application | None:
    cache = _cache(db)
    if cache is None:
        return get_application_by_number(db, application_number)
    return cache["applications"].get(application_number)


def mark_by_campus_and_course(
    db: Session, campus_id: str, course_code: str
) -> ApplicantMark | None:
    cache = _cache(db)
    if cache is None:
        return get_applicant_mark_by_campus_and_course(db, campus_id, course_code)
    return cache["marks"].get((campus_id, course_code))


def motivation_by_campus_id(db: Session, campus_id: str) -> Motivation | None:
    cache = _cache(db)
    if cache is None:
        return get_motivation_by_campus_id(db, campus_id)
    return cache["motivations"].get(campus_id)


def remember_applicant(db: Session, applicant: Applicant) -> None:
    cache = _cache(db)
    if cache is not None:
        cache["applicants"][applicant.campus_id] = applicant


def remember_application(db: Session, application: Application) -> None:
    cache = _cache(db)
    if cache is not None:
        cache["applications"][application.application_number] = application


def remember_mark(db: Session, mark: ApplicantMark) -> None:
    cache = _cache(db)
    if cache is not None:
        cache["marks"][(mark.campus_id, mark.course_code)] = mark


def remember_motivation(db: Session, motivation: Motivation) -> None:
    cache = _cache(db)
    if cache is not None:
        cache["motivations"][motivation.campus_id] = motivation


def active_applications_for(
    db: Session, campus_id: str, application_date: date
) -> list[Application]:
    """Applications for one applicant in the given year.

    Served from the cache when primed. Duplicate detection only ever asks
    about the row's own applicant, and the prefetch already holds every
    application the sheet mentions plus any created during the run.
    """
    cache = _cache(db)
    if cache is None:
        from app.queries.applications import get_active_applications_by_campus_ids

        return get_active_applications_by_campus_ids(db, [campus_id], application_date)
    return [
        application
        for application in cache["applications"].values()
        if application.campus_id == campus_id
        and application.application_date is not None
        and application.application_date.year == application_date.year
    ]
