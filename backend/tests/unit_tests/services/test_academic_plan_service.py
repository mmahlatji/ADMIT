import pytest
from unittest.mock import Mock

from app.queries.academic_plan_repository import AcademicPlanRepository
from app.services.academic_plan_service import AcademicPlanService
from app.models import AcademicPlan
from app.schemas.academic_plans import AcademicPlanCreate

@pytest.fixture
def repository():
    return Mock(spec=AcademicPlanRepository)


@pytest.fixture
def service(repository):
    return AcademicPlanService(repository)


def test_get_by_id(service, repository):
    expected = Mock(spec=AcademicPlan) # Mock the expected return type

    repository.get_by_id.return_value = expected # Mock the expected return value

    result = service.get_by_id(1) # call the service

    assert result is expected
    repository.get_by_id.assert_called_once_with(1)


def test_get_all_returns_list(service, repository):
    expected = [
        AcademicPlan(academic_plan_id=1, academic_plan="csc06", academic_program_code="csc"),
        AcademicPlan(academic_plan_id=2, academic_plan="csc05", academic_program_code="csc")
    ]

    repository.get_all.return_value = expected

    result = service.get_all()

    assert result == expected
    assert type(result) is list
    repository.get_all.assert_called_once()


def test_add(service, repository):
    data = AcademicPlanCreate(
        academic_plan="csc06",
        academic_program_code="csc"
    )

    service.add(data)
    repository.add.assert_called_once()

    academic_plan = repository.add.call_args.args[0] # the first argument passed to the add method

    assert isinstance(academic_plan, AcademicPlan)