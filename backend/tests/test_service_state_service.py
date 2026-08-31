import uuid
from datetime import date

from app.models.applications import Application, ApplicationStatus, Choice
from app.services.state.application_state_service import (
    determine_duplicate,
    compute_incorrect_and_requires_plan_change_flags,
)


def _make_application(academic_plan1: str, incorrect_plan: bool = False):
    return Application(
        application_id=uuid.uuid4(),
        application_number="100001",
        campus_id="TEST001",
        academic_program_code="SH001",
        academic_plan1=academic_plan1,
        choice=Choice.FIRST,
        application_date=date(2022, 4, 3),
        effective_date=date(2022, 10, 24),
        application_status=ApplicationStatus.APPLIED,
        incorrect_plan=incorrect_plan,
    )

def test_determine_duplicate_same_department_wrong_plan_first():
    first = _make_application("SH001CSC05", incorrect_plan=True)
    second = _make_application("SH001CSC06")
    assert determine_duplicate([first, second]) is first


def test_determine_duplicate_same_department_wrong_plan_second():
    first = _make_application("SH001CSC05")
    second = _make_application("SH001CSC06", incorrect_plan=True)
    assert determine_duplicate([first, second]) is second


def test_determine_duplicate_different_department():
    first = _make_application("SH001CSC05", incorrect_plan=True)
    second = _make_application("SH001MAM05")
    assert determine_duplicate([first, second]) is None


def test_determine_duplicate_neither_incorrect():
    first = _make_application("SH001CSC05")
    second = _make_application("SH001CSC06")
    assert determine_duplicate([first, second]) is None



def test_compute_incorrect_no_external_plan():
    assert compute_incorrect_and_requires_plan_change_flags(
        "SH001CSC05", None, "SH001CSC05", None
    ) == (False, False)


def test_compute_incorrect_uct_student_on_external_plan():
    assert compute_incorrect_and_requires_plan_change_flags(
        "SH001CSC06", "2022:SB001:some registration", "SH001CSC05", "SH001CSC06"
    ) == (True, True)


def test_compute_incorrect_uct_student_on_internal_plan():
    assert compute_incorrect_and_requires_plan_change_flags(
        "SH001CSC05", "2022:SB001:some registration", "SH001CSC05", "SH001CSC06"
    ) == (False, False)


def test_compute_incorrect_non_uct_student_on_internal_plan():
    assert compute_incorrect_and_requires_plan_change_flags(
        "SH001CSC05", " ", "SH001CSC05", "SH001CSC06"
    ) == (True, True)


def test_compute_incorrect_non_uct_student_on_external_plan():
    assert compute_incorrect_and_requires_plan_change_flags(
        "SH001CSC06", None, "SH001CSC05", "SH001CSC06"
    ) == (False, False)
