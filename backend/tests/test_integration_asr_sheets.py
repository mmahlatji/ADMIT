"""End-to-end test that runs the two real ASR sheets through the import
pipeline, October first then December, against an in-memory DB seeded with the
CSC department, its internal/external plans, and an upload user.

These sheets live in the repo root and are not committed; the test skips if
they are absent, and requires openpyxl to read .xlsx.
"""

from pathlib import Path

import pandas as pd
import pytest

from app.models.academic_plans import AcademicPlanType
from app.models.applications import ApplicationStatus
from app.models.import_runs import ImportStatus, SourceType
from app.queries.academic_plans import create_academic_plan
from app.queries.applicants import get_applicant_by_campus_id
from app.queries.applications import get_application_by_number
from app.queries.departments import create_department
from app.services.import_runs import create_import_run
from app.services.imports.orchestrator import run_import
from tests.test_queries_notes import _create_author

UPLOADED_BY = "9999999"


def _make_import_run(db_session, source_type, file_name, sheet):
    return create_import_run(
        db_session,
        source_type=source_type,
        uploaded_by=UPLOADED_BY,
        file_name=file_name,
        status=ImportStatus.PROCESSING,
        rows_total=len(sheet),
    )

_REPO_ROOT = Path(__file__).resolve().parents[2]
_OCTOBER = _REPO_ROOT / "CSC - ASR - 2023 - October 2022.xlsx"
_DECEMBER = _REPO_ROOT / "CSC - ASR - 2023 - December 2022.xlsx"



def _seed(db):
    _create_author(db, employee_id=UPLOADED_BY)
    create_department(db, "CSC", "Computer Science")
    create_academic_plan(db, "CSC", "SH001CSC05", AcademicPlanType.INTERNAL)
    create_academic_plan(db, "CSC", "SH001CSC06", AcademicPlanType.EXTERNAL)





def test_real_asr_sheets_import_sequentially(db_session):
    pytest.importorskip("openpyxl")
    if not (_OCTOBER.exists() and _DECEMBER.exists()):
        pytest.skip("real ASR sheets not present in the repo root")

    _seed(db_session)

    oct_sheet = pd.read_excel(_OCTOBER)
    oct_run = run_import(
        db_session,
        _make_import_run(db_session, SourceType.ASR, "CSC - ASR - 2023 - October 2022.xlsx", oct_sheet),
        oct_sheet,
    )
    assert oct_run.status == ImportStatus.COMPLETED
    assert oct_run.rows_total == 345
    assert oct_run.rows_loaded > 0
    assert oct_run.rows_loaded + oct_run.rows_rejected  + oct_run.rows_flagged == oct_run.rows_total

    applicant = get_applicant_by_campus_id(db_session, "MLKRAN020")
    assert applicant is not None
    # Malik is a non-UCT student (blank last registration) who applied to both
    # plans in one cycle. The internal plan is the wrong one, so duplicate
    # detection denies it and keeps the external-plan application applied.
    incorrect = get_application_by_number(db_session, "1472579")
    assert incorrect.application_status == ApplicationStatus.DENIED
    assert incorrect.duplicate_application is True
    assert get_application_by_number(db_session, "1536605").application_status == ApplicationStatus.APPLIED

    dec_sheet = pd.read_excel(_DECEMBER)
    dec_run = run_import(
        db_session,
        _make_import_run(db_session, SourceType.ASR, "CSC - ASR - 2023 - December 2022.xlsx", dec_sheet),
        dec_sheet,
    )
    assert dec_run.status == ImportStatus.COMPLETED
    assert dec_run.rows_total == 383
    assert dec_run.rows_loaded + dec_run.rows_rejected + dec_run.rows_flagged == dec_run.rows_total

    # the October applicant is reused, not duplicated ...
    assert get_applicant_by_campus_id(db_session, "MLKRAN020").applicant_id == applicant.applicant_id
    # ... and December's decisions now apply across the gap: the correct
    # application moves APPLIED -> DENIED (DENY/COMP), while the duplicate one
    # stays DENIED via the terminal identity loop.
    assert (
        get_application_by_number(db_session, "1472579").application_status
        == ApplicationStatus.DENIED
    )
    assert (
        get_application_by_number(db_session, "1536605").application_status
        == ApplicationStatus.DENIED
    )
    
  

### These are just for accounting


# _HONOURS = _REPO_ROOT / "HonoursApplicationProcessing December 2022.xlsx"

# # An IT/CS offer maps onto any of these statuses: made (CONDITIONAL_OFFER /
# # ACCEPTED), accepted (READY_TO_REGISTER), or declined (CANCELLED). Grouping
# # them is what makes our more-granular system provably consistent with the
# # Decision column.
# _OFFER_STATUSES = {
#     ApplicationStatus.CONDITIONAL_OFFER,
#     ApplicationStatus.ACCEPTED,
#     ApplicationStatus.READY_TO_REGISTER,
#     ApplicationStatus.CANCELLED,
# }

# # The exact (campus_id, plan) rows where the IT/CS decision or
# # the ASR effective date diverges from our rules engine. These are NOT mapping
# # errors (the mapping is unit-proven in test_services_import_application_state);
# # they are data artifacts of doing the IT/CS processing by hand.
# _EXPECTED_ANOMALIES = {
#     ("BTHTHU003", "SH001CSC05"),
#     ("CSSRAS002", "SH001CSC06"),
#     ("DTTJAM001", "SH001CSC05"),
#     ("ERSCHR018", "SH001CSC06"),
#     ("KRGMAR001", "SH001CSC05"),
#     ("MBSNOM002", "SH001CSC05"),
#     ("TSHNAL005", "SH001CSC05"),
# }

# def _counters(run) -> str:
#     return (
#         f"total={run.rows_total}  loaded={run.rows_loaded}  rejected={run.rows_rejected}"
#         f"  new={run.rows_auto_new}  matched={run.rows_auto_matched}  flagged={run.rows_flagged}"
#     )


# def _print_report(sections):
#     """Print an aligned two-column report: each section is (title, [(label, value)])."""
#     print()
#     print("=" * 78)
#     for title, rows in sections:
#         print(f"  {title}")
#         width = max((len(label) for label, _ in rows), default=0)
#         for label, value in rows:
#             print(f"    {label:<{width}}  {value}")
#         print()
#     print("=" * 78)
#     print()

# def _read_decisions(path: Path) -> dict[tuple[str, str], str]:
#     """Read  IT/CS decisions: (campus_id, plan) -> decision.

#     The Decisions sheets are two side-by-side tables with a duplicated "Campus
#     Id" header; the per-plan detail table is the second one (Campus Id.1 /
#     Academic Plan / Decision). A decision made on a later date overrides an
#     earlier one for the same (campus_id, plan).
#     """
#     decisions: dict[tuple[str, str], str] = {}
#     for date in ("2022-10-19", "2022-10-31", "2022-11-07", "2022-12-05"):
#         df = pd.read_excel(path, sheet_name=f"Decisions-{date}")
#         for _, row in df.iterrows():
#             campus = str(row["Campus Id.1"]).strip()
#             plan = str(row["Academic Plan"]).strip()
#             decision = str(row["Decision"]).strip()
#             if campus and plan and decision and decision != "nan":
#                 decisions[(campus, plan)] = decision
#     return decisions


# def _flagged_reasons(db) -> dict[tuple[str, str], str]:
#     """Map (campus_id, plan) -> flag reason for every row the import flagged.

#     A flagged row opens a MatchingReview linked to its staging row; the reason
#     recorded there (and on staging.rejection_reason) is what a reviewer sees.
#     """
#     staging_by_id = {s.staging_id: s for s in db.scalars(select(Staging))}
#     flagged: dict[tuple[str, str], str] = {}
#     for review in db.scalars(select(MatchingReview)):
#         raw = staging_by_id[review.staging_row_id].raw_data
#         campus = str(raw.get("Campus Id", "")).strip()
#         plan = str(raw.get("Academic Plan 1", "")).strip()
#         if campus and plan:
#             flagged[(campus, plan)] = review.reason or ""
#     return flagged


# def test_decisions_are_consistent_with_it_cs_processing(db_session):
#     pytest.importorskip("openpyxl")
#     if not (_OCTOBER.exists() and _DECEMBER.exists() and _HONOURS.exists()):
#         pytest.skip("real ASR sheets / honours workbook not present in the repo root")

#     _seed(db_session)

#     oct_df = pd.read_excel(_OCTOBER)
#     dec_df = pd.read_excel(_DECEMBER)

#     oct_run = run_import(db_session, SourceType.ASR, UPLOADED_BY, "oct.xlsx", oct_df)
#     dec_run = run_import(db_session, SourceType.ASR, UPLOADED_BY, "dec.xlsx", dec_df)

#     # what our system actually stored, keyed the same way as the decisions
#     imported = {
#         (app.campus_id, app.academic_plan1): app.application_status
#         for app in db_session.scalars(select(Application))
#     }
#     status_dist = Counter(status.value for status in imported.values())

#     # per (campus_id, plan): ASR action/reason + effective date from each export
#     actions: dict[tuple[str, str], str] = {}
#     reasons: dict[tuple[str, str], str] = {}
#     oct_eff: dict[tuple[str, str], str] = {}
#     dec_eff: dict[tuple[str, str], str] = {}
#     for _, row in oct_df.iterrows():
#         key = (str(row["Campus Id"]).strip(), str(row["Academic Plan 1"]).strip())
#         oct_eff[key] = str(row["Effective Date"]).strip()
#     for _, row in dec_df.iterrows():
#         key = (str(row["Campus Id"]).strip(), str(row["Academic Plan 1"]).strip())
#         actions[key] = str(row["Program Action"]).strip()
#         reasons[key] = str(row["Program Reason"]).strip()
#         dec_eff[key] = str(row["Effective Date"]).strip()

#     decisions = _read_decisions(_HONOURS)

#     # IT/CS decision distribution, with the reasons folded away as instructed
#     decision_dist: Counter[str] = Counter()
#     for decision in decisions.values():
#         d = decision.lower()
#         if d.startswith("deny"):
#             decision_dist["Deny"] += 1
#         elif d.startswith("firm offer"):
#             decision_dist["Firm Offer"] += 1
#         elif d.startswith("conditional offer"):
#             decision_dist["Conditional Offer"] += 1
#         else:
#             decision_dist[decision] += 1

#     matched: Counter[str] = Counter()
#     pending: list[tuple[str, str]] = []
#     anomalies: list[tuple[str, str]] = []

#     for (campus, plan), decision in sorted(decisions.items()):
#         decision_lower = decision.lower()
#         status = imported.get((campus, plan))
#         action = actions.get((campus, plan), "")

#         if status is None:
#             anomalies.append((campus, plan))
#         elif decision_lower.startswith("deny"):
#             if status is ApplicationStatus.DENIED:
#                 matched["deny"] += 1
#             elif status is ApplicationStatus.APPLIED and action == "DDEF":
#                 pending.append((campus, plan))
#             else:
#                 anomalies.append((campus, plan))
#         elif decision_lower.startswith(("firm offer", "conditional offer")):
#             if status in _OFFER_STATUSES:
#                 matched["offer"] += 1
#             elif status is ApplicationStatus.APPLIED and action == "DDEF":
#                 pending.append((campus, plan))
#             else:
#                 anomalies.append((campus, plan))
#         else:
#             anomalies.append((campus, plan))

#     # every "pending" row is provable ASR staleness, not a mapping error
#     for campus, plan in pending:
#         assert actions.get((campus, plan)) == "DDEF", (
#             f"pending row {campus}/{plan} is not DDEF staleness"
#         )

#     # the only divergences are the known hand-processing artifacts
#     assert set(anomalies) == _EXPECTED_ANOMALIES

#     def _explain(campus, plan) -> str:
#         """Human-readable reason for one anomaly / pending row."""
#         decision = decisions[(campus, plan)]
#         status = imported.get((campus, plan))
#         status_label = status.value if status is not None else "missing"
#         action = actions.get((campus, plan), "—")
#         reason = reasons.get((campus, plan), "—")
#         oeff = oct_eff.get((campus, plan), "")
#         deff = dec_eff.get((campus, plan), "")

#         is_offer = decision.lower().startswith(("firm offer", "conditional offer"))
#         if is_offer and status is ApplicationStatus.DENIED:
#             cause = "wrong-plan application denied as duplicate (IT/CS offered it)"
#         elif oeff and deff and deff != "nan" and oeff != "nan" and deff < oeff:
#             cause = f"stale effective date (Dec {deff} < Oct {oeff})"
#         elif action == "DDEF":
#             cause = "ASR still DDEF/HOD (referred) — decision not yet in the ASR export"
#         elif status is ApplicationStatus.APPLIED:
#             cause = f"ASR {action}/{reason} not applied"
#         else:
#             cause = f"ASR {action}/{reason} disagrees with decision"
#         return f"IT/CS {decision!r} vs stored {status_label!r} — {cause}"

#     flagged = _flagged_reasons(db_session)
#     flagged_rows = [
#         (f"{campus}/{plan}", reason)
#         for (campus, plan), reason in sorted(flagged.items())
#     ]
#     unflagged = [
#         (campus, plan)
#         for campus, plan in sorted(set(anomalies) | set(pending))
#         if (campus, plan) not in flagged
#     ]

#     _print_report(
#         [
#             (
#                 "IMPORT RUNS",
#                 [
#                     ("October", _counters(oct_run)),
#                     ("December", _counters(dec_run)),
#                 ],
#             ),
#             (
#                 "IT/CS DECISION SHEETS (per plan, latest date wins)",
#                 [
#                     ("Deny", decision_dist["Deny"]),
#                     ("Conditional Offer", decision_dist["Conditional Offer"]),
#                     ("Firm Offer", decision_dist["Firm Offer"]),
#                     ("total decisions", sum(decision_dist.values())),
#                 ],
#             ),
#             (
#                 "OUR SYSTEM (final statuses, all applications)",
#                 [
#                     *[(label, count) for label, count in status_dist.most_common()],
#                     ("total applications", sum(status_dist.values())),
#                 ],
#             ),
#             (
#                 "CROSS-REFERENCE (decisions vs our statuses)",
#                 [
#                     ("matched — deny", matched["deny"]),
#                     ("matched — offer", matched["offer"]),
#                     ("pending (ASR DDEF/HOD)", len(pending)),
#                     ("anomalies (hand-processing)", len(anomalies)),
#                 ],
#             ),
#             (
#                 "WHY WE'RE OFF (anomalies and pending, one line each)", ## this will tell us what we need to flag for review

#                 [
#                     *[(f"{campus}/{plan} (anomaly)", _explain(campus, plan)) for campus, plan in sorted(anomalies)],
#                     *[(f"{campus}/{plan} (pending)", _explain(campus, plan)) for campus, plan in sorted(pending)],
#                 ],
#             ),
#             (
#                 "FLAG REASONS (matching reviews)",
#                 [
#                     *flagged_rows,
#                     ("total flagged reviews", len(flagged_rows)),
#                     ("-----", "-----"),
#                     ("anomalies/pending NOT flagged", len(unflagged)),
#                     *[(f"{campus}/{plan}", _explain(campus, plan)) for campus, plan in unflagged],
#                 ],
#             ),
#             (
#                 "Where the system loses aplications (Cross-referencing mismatch)",
#                 "- The asr ingestion pipeline auto denies duplicate applications and flags incorrect applications,",
#                 "- Anomalies of DTTJAM001, ERSCHR018, MBSNOM002 are related to the IT/CS Application Processing having made decisions on duplicated applications,",
#                 "- ANDDAN001, FRSRYA001 are shown to have a pending offer in the processing sheets, but the state is never updated by the asr sheet",
#                 "- Some have stale effective dates but the application status is still updated"
#                 "- 9 entries are pending a denial but the status in the December asr is never advanced."
#                 "---------",
#                 "Where there are gains."
#                 "- There are 262 decisions in the decision sheets but 392 applications in the ASR."
#             )
#         ]
#     )
