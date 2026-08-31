
from pathlib import Path

import pandas as pd
import pytest

from app.models.academic_plans import AcademicPlanType
from app.models.import_runs import ImportStatus, SourceType
from app.queries.academic_plans import create_academic_plan
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
# Order doesnt matter as long as it works
_OCTOBER = _REPO_ROOT / "CSC - ASR - 2023 - October 2022.xlsx"
_DECEMBER = _REPO_ROOT / "CSC - ASR - 2023 - December 2022.xlsx"
_UCT_MARKS = _REPO_ROOT / "UCT Applicant Marks - December 2022.xlsx"


def _seed(db):
    _create_author(db, employee_id=UPLOADED_BY)
    create_department(db, "CSC", "Computer Science")
    create_academic_plan(db, "CSC", "SH001CSC05", AcademicPlanType.INTERNAL)
    create_academic_plan(db, "CSC", "SH001CSC06", AcademicPlanType.EXTERNAL)

def test_real_uct_marks_sheet_import(db_session):
    pytest.importorskip("openpyxl")
    if not (_OCTOBER.exists() and _DECEMBER.exists() and _UCT_MARKS.exists()):
        pytest.skip("Required files ASR October, December and UCT marks dont exist.")

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


    dec_sheet = pd.read_excel(_DECEMBER)
    dec_run = run_import(
        db_session,
        _make_import_run(db_session, SourceType.ASR, "CSC - ASR - 2023 - December 2022.xlsx", dec_sheet),
        dec_sheet,
    )
    assert dec_run.status == ImportStatus.COMPLETED
    assert dec_run.rows_total == 383
    assert dec_run.rows_loaded + dec_run.rows_rejected + dec_run.rows_flagged == dec_run.rows_total

    marks_sheet = pd.read_excel(_UCT_MARKS)
    marks_run = run_import(
        db_session,
        _make_import_run(db_session, SourceType.UCT_MARKS, "UCT Applicant Marks - December 2022.xlsx", marks_sheet), 
        marks_sheet
    )

    assert marks_run.status == ImportStatus.COMPLETED
    
  