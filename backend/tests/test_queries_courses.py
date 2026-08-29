from app.queries.courses import (
    create_course,
    delete_course,
    get_course_by_id,
    get_courses,
    update_course,
)
from app.queries.departments import create_department


def test_create_and_get_course(db_session):
    create_department(db_session, "CSC")
    course = create_course(db_session, "CSC", "CSC2001F", "Computer Science I")

    fetched = get_course_by_id(db_session, course.course_id)
    assert fetched is not None
    assert fetched.course_code == "CSC2001F"


def test_get_courses_returns_all(db_session):
    create_department(db_session, "CSC")
    create_course(db_session, "CSC", "CSC2001F")
    create_course(db_session, "CSC", "CSC2002S")

    assert len(get_courses(db_session)) == 2


def test_update_course_only_sets_passed_fields(db_session):
    create_department(db_session, "CSC")
    course = create_course(db_session, "CSC", "CSC2001F", "Old Name")

    updated = update_course(db_session, course, course_name="New Name")
    assert updated.course_code == "CSC2001F"
    assert updated.course_name == "New Name"


def test_delete_course(db_session):
    create_department(db_session, "CSC")
    course = create_course(db_session, "CSC", "CSC2001F")

    delete_course(db_session, course)

    assert get_course_by_id(db_session, course.course_id) is None
