from app.queries.departments import (
    create_department,
    delete_department,
    get_department_by_id,
    get_departments,
    update_department,
)


def test_create_and_get_department(db_session):
    department = create_department(db_session, "CSC", "Computer Science")

    fetched = get_department_by_id(db_session, department.department_id)
    assert fetched is not None
    assert fetched.department_code == "CSC"
    assert fetched.department_name == "Computer Science"


def test_get_departments_returns_all(db_session):
    create_department(db_session, "CSC")
    create_department(db_session, "MAM")

    departments = get_departments(db_session)
    assert len(departments) == 2


def test_update_department_only_sets_passed_fields(db_session):
    department = create_department(db_session, "CSC", "Computer Science")

    updated = update_department(db_session, department, department_name="CS")
    assert updated.department_code == "CSC"
    assert updated.department_name == "CS"


def test_delete_department(db_session):
    department = create_department(db_session, "CSC")

    delete_department(db_session, department)

    assert get_department_by_id(db_session, department.department_id) is None
