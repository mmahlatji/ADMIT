from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.models.applicant_marks import ResultCode
from app.models.applicants import CitizenshipResidency, TitleEnum
from app.models.departments import Department
from app.models.users import RoleEnum
from app.queries.applicant_marks import create_applicant_mark
from app.queries.applicants import create_applicant
from app.queries.courses import create_course
from app.queries.departments import create_department
from app.queries.nl_query import execute_query
from app.services.nl_query import describe_schema


@pytest.fixture
def departments(db_session):
    create_department(db_session, "CSC", "Computer Science")
    create_department(db_session, "MAM", "Mathematics")
    create_course(db_session, "CSC", "CSC1015F", "Intro CS")
    create_course(db_session, "CSC", "CSC2001F", "Data Structures")
    create_course(db_session, "MAM", "MAM1000W", "Math 1")
    db_session.commit()
    return db_session


@pytest.fixture
def marks(db_session):
    create_applicant(
        db_session,
        campus_id="xxxyyy001",
        employee_id="1000001",
        title=TitleEnum.MS,
        first_name="Noah",
        last_name="Smith",
        citizenship_residency=CitizenshipResidency.SA_CITIZEN,
    )
    create_applicant(
        db_session,
        campus_id="xxxyyy002",
        employee_id="1000002",
        title=TitleEnum.MR,
        first_name="Ava",
        last_name="Jones",
        citizenship_residency=CitizenshipResidency.SA_CITIZEN,
    )
    create_applicant_mark(db_session, "xxxyyy001", "CSC1015F", 60, ResultCode.PA)
    create_applicant_mark(db_session, "xxxyyy001", "CSC2001F", 80, ResultCode.PA)
    create_applicant_mark(db_session, "xxxyyy002", "CSC1015F", 40, ResultCode.PA)
    db_session.commit()
    return db_session


def test_describe_schema_includes_tables_and_foreign_keys():
    schema = describe_schema(RoleEnum.convenor)
    assert "departments" in schema["tables"]
    assert "courses" in schema["tables"]
    assert "department_code" in schema["tables"]["departments"]["columns"]
    fks = schema["tables"]["courses"]["foreign_keys"]
    assert {"column": "department_code", "references": "departments.department_code"} in fks


def test_count_all(departments):
    assert execute_query({"base_table": "departments", "action": "count"}, departments) == 2


def test_invalid_operator_rejected(departments):
    with pytest.raises(ValidationError):
        execute_query(
            {
                "base_table": "departments",
                "filters": [{"field": "department_code", "op": "bogus", "value": "CSC"}],
            },
            departments,
        )


def test_unknown_key_rejected(departments):
    with pytest.raises(ValidationError):
        execute_query({"base_table": "departments", "action": "count", "bogus": True}, departments)


def test_count_with_filter(departments):
    spec = {
        "base_table": "departments",
        "action": "count",
        "filters": [{"field": "department_code", "op": "eq", "value": "CSC"}],
    }
    assert execute_query(spec, departments) == 1


def test_count_with_join_and_filter(departments):
    spec = {
        "base_table": "departments",
        "action": "count",
        "joins": [{"table": "courses"}],
        "filters": [{"table": "courses", "field": "course_code", "op": "eq", "value": "CSC1015F"}],
    }
    assert execute_query(spec, departments) == 1


def test_count_with_distinct_field(marks):
    spec = {
        "base_table": "applicant_marks",
        "action": "count",
        "field": "campus_id",
        "distinct": True,
    }
    assert execute_query(spec, marks) == 2


def test_select_distinct_rows(marks):
    # CSC1015F appears twice, so without dedup this returns three rows.
    spec = {
        "base_table": "applicant_marks",
        "select": [{"field": "course_code"}],
        "distinct_rows": True,
        "order_by": [{"field": "course_code", "direction": "asc"}],
    }
    assert [r["course_code"] for r in execute_query(spec, marks)] == ["CSC1015F", "CSC2001F"]


def test_select_join_returns_rows(departments):
    spec = {
        "base_table": "courses",
        "joins": [{"table": "departments"}],
        "select": [
            {"table": "courses", "field": "course_code"},
            {"table": "departments", "field": "department_name", "alias": "dept"},
        ],
        "order_by": [{"field": "course_code", "direction": "asc"}],
    }
    rows = execute_query(spec, departments)
    assert [row["course_code"] for row in rows] == ["CSC1015F", "CSC2001F", "MAM1000W"]
    assert rows[0]["dept"] == "Computer Science"


def test_explicit_on_join(departments):
    spec = {
        "base_table": "departments",
        "action": "count",
        "joins": [{"table": "courses", "on": "departments.department_code=courses.department_code"}],
        "filters": [{"table": "courses", "field": "course_name", "op": "like", "value": "%CS%"}],
    }
    assert execute_query(spec, departments) == 1


def test_group_by_count(marks):
    spec = {
        "base_table": "applicant_marks",
        "select": [
            {"field": "campus_id"},
            {"func": "count", "field": "mark", "alias": "n"},
        ],
        "group_by": ["campus_id"],
        "order_by": [{"field": "campus_id", "direction": "asc"}],
    }
    rows = execute_query(spec, marks)
    assert rows == [
        {"campus_id": "xxxyyy001", "n": 2},
        {"campus_id": "xxxyyy002", "n": 1},
    ]


def test_aggregate_avg_and_max(marks):
    spec = {
        "base_table": "applicant_marks",
        "select": [
            {"func": "avg", "field": "mark", "alias": "avg_mark"},
            {"func": "max", "field": "mark", "alias": "max_mark"},
        ],
    }
    rows = execute_query(spec, marks)
    assert rows == [{"avg_mark": 60.0, "max_mark": 80}]


def test_group_by_auto_includes_plain_columns(marks):
    # LLM groups only by campus_id but also selects first/last name; the executor
    # must add the non-aggregated columns to GROUP BY instead of failing.
    spec = {
        "base_table": "applicant_marks",
        "joins": [{"table": "applicants", "on": "applicant_marks.campus_id=applicants.campus_id"}],
        "select": [
            {"table": "applicants", "field": "first_name"},
            {"table": "applicants", "field": "last_name"},
            {"func": "count", "table": "applicant_marks", "field": "mark_id", "alias": "number of marks"},
        ],
        "group_by": ["applicants.campus_id"],
        "order_by": [{"field": "applicants.campus_id", "direction": "asc"}],
    }
    assert execute_query(spec, marks) == [
        {"first_name": "Noah", "last_name": "Smith", "number of marks": 2},
        {"first_name": "Ava", "last_name": "Jones", "number of marks": 1},
    ]


def test_order_by_unresolvable_column_falls_back(marks):
    # The LLM ordered by applicant_id, a column of `applicants` that isn't in
    # this query's tables; the executor falls back to the group key.
    spec = {
        "base_table": "applicant_marks",
        "select": [
            {"field": "campus_id", "alias": "Applicant ID"},
            {"func": "count", "field": "mark_id", "distinct": True, "alias": "Number of Marks"},
        ],
        "group_by": ["campus_id"],
        "order_by": [{"field": "applicant_id", "direction": "asc"}],
    }
    assert execute_query(spec, marks) == [
        {"Applicant ID": "xxxyyy001", "Number of Marks": 2},
        {"Applicant ID": "xxxyyy002", "Number of Marks": 1},
    ]


def test_distinct_rows_order_by_non_selected_column_falls_back(marks):
    # SELECT DISTINCT forbids ordering by a column outside the select list.
    spec = {
        "base_table": "applicant_marks",
        "select": [{"field": "course_code"}],
        "distinct_rows": True,
        "order_by": [{"field": "campus_id", "direction": "asc"}],
    }
    assert [r["course_code"] for r in execute_query(spec, marks)] == ["CSC1015F", "CSC2001F"]


def test_group_by_order_by_ungrouped_column_falls_back(marks):
    # last_name is resolvable (applicants is joined) but not grouped; the
    # executor falls back to the group key instead of raising a GroupingError.
    spec = {
        "base_table": "applicant_marks",
        "joins": [{"table": "applicants", "on": "applicant_marks.campus_id=applicants.campus_id"}],
        "select": [
            {"table": "applicant_marks", "field": "campus_id"},
            {"func": "count", "field": "mark", "alias": "n"},
        ],
        "group_by": ["applicant_marks.campus_id"],
        "order_by": [{"field": "last_name", "direction": "asc"}],
    }
    assert execute_query(spec, marks) == [
        {"campus_id": "xxxyyy001", "n": 2},
        {"campus_id": "xxxyyy002", "n": 1},
    ]


def test_avg_on_non_numeric_column_raises(marks):
    spec = {"base_table": "applicants", "select": [{"func": "avg", "field": "first_name"}]}
    with pytest.raises(ValueError, match="requires a numeric column"):
        execute_query(spec, marks)


def test_select_all_columns(departments):
    rows = execute_query({"base_table": "departments"}, departments)
    assert len(rows) == 2
    assert set(rows[0]) == {"department_code", "department_name"}


def test_unknown_table_raises(departments):
    with pytest.raises(ValueError, match="Unknown table"):
        execute_query({"base_table": "not_a_table", "action": "count"}, departments)


def test_unknown_column_raises(departments):
    spec = {
        "base_table": "departments",
        "action": "count",
        "filters": [{"field": "does_not_exist", "op": "eq", "value": 1}],
    }
    with pytest.raises(ValueError, match="Unknown column"):
        execute_query(spec, departments)


def test_unknown_operator_raises(departments):
    spec = {
        "base_table": "departments",
        "action": "count",
        "filters": [{"field": "department_code", "op": "hax", "value": "CSC"}],
    }
    with pytest.raises(ValidationError):
        execute_query(spec, departments)


def test_unknown_aggregate_raises(marks):
    spec = {
        "base_table": "applicant_marks",
        "select": [{"func": "median", "field": "mark"}],
    }
    with pytest.raises(ValidationError):
        execute_query(spec, marks)


def test_missing_foreign_key_join_raises(departments):
    # applicant_marks has no FK to departments, so the auto-resolve must fail.
    spec = {"base_table": "departments", "joins": [{"table": "applicant_marks"}], "action": "count"}
    with pytest.raises(ValueError, match="No join condition"):
        execute_query(spec, departments)


def test_aggregate_requires_field_for_non_count(marks):
    spec = {"base_table": "applicant_marks", "select": [{"func": "avg"}]}
    with pytest.raises(ValueError, match="requires a 'field'"):
        execute_query(spec, marks)


def test_select_omits_uuid_columns(departments):
    rows = execute_query({"base_table": "departments"}, departments)
    assert "department_id" not in rows[0]
    assert set(rows[0]) == {"department_code", "department_name"}


def test_filter_uuid_from_string(departments):
    target = str(departments.scalar(select(Department.department_id)))
    spec = {
        "base_table": "departments",
        "action": "count",
        "filters": [{"field": "department_id", "op": "eq", "value": target}],
    }
    assert execute_query(spec, departments) == 1


def test_filter_integer_from_string(marks):
    spec = {
        "base_table": "applicant_marks",
        "action": "count",
        "filters": [{"field": "mark", "op": "gte", "value": "50"}],
    }
    assert execute_query(spec, marks) == 2


def test_in_operator_coerces_each_element(marks):
    spec = {
        "base_table": "applicant_marks",
        "action": "count",
        "filters": [{"field": "mark", "op": "in", "value": ["60", "80"]}],
    }
    assert execute_query(spec, marks) == 2


def test_filter_enum_from_string(marks):
    spec = {
        "base_table": "applicants",
        "action": "count",
        "filters": [{"field": "citizenship_residency", "op": "eq", "value": "SA Citizen"}],
    }
    assert execute_query(spec, marks) == 2


def test_filter_date_from_string(db_session):
    applicant = create_applicant(
        db_session,
        campus_id="xxxyyy001",
        employee_id="1000001",
        title=TitleEnum.MS,
        first_name="Noah",
        last_name="Smith",
        citizenship_residency=CitizenshipResidency.SA_CITIZEN,
    )
    applicant.birth_date = date(1995, 5, 5)
    db_session.commit()

    spec = {
        "base_table": "applicants",
        "action": "count",
        "filters": [{"field": "birth_date", "op": "gte", "value": "1990-01-01"}],
    }
    assert execute_query(spec, db_session) == 1


def test_invalid_uuid_value_raises(departments):
    spec = {
        "base_table": "departments",
        "action": "count",
        "filters": [{"field": "department_id", "op": "eq", "value": "not-a-uuid"}],
    }
    with pytest.raises(ValueError, match="Invalid UUID"):
        execute_query(spec, departments)


def test_invalid_integer_value_raises(marks):
    spec = {
        "base_table": "applicant_marks",
        "action": "count",
        "filters": [{"field": "mark", "op": "eq", "value": "abc"}],
    }
    with pytest.raises(ValueError, match="Invalid Integer"):
        execute_query(spec, marks)


def test_invalid_date_value_raises(db_session):
    spec = {
        "base_table": "applicants",
        "action": "count",
        "filters": [{"field": "birth_date", "op": "eq", "value": "not-a-date"}],
    }
    with pytest.raises(ValueError, match="Invalid Date"):
        execute_query(spec, db_session)


def test_invalid_enum_value_raises(marks):
    spec = {
        "base_table": "applicants",
        "action": "count",
        "filters": [{"field": "citizenship_residency", "op": "eq", "value": "Martian"}],
    }
    with pytest.raises(ValueError, match="Invalid value"):
        execute_query(spec, marks)


def test_execute_query_rejects_disallowed_table(db_session):
    spec = {"base_table": "users", "action": "count"}
    with pytest.raises(ValueError, match="not available"):
        execute_query(spec, db_session, allowed_tables={"applicants"})


def test_execute_query_allows_listed_table(db_session):
    spec = {"base_table": "departments", "action": "count"}
    assert execute_query(spec, db_session, allowed_tables={"departments"}) == 0


def test_auto_join_ambiguous_raises(db_session):
    # staging has FKs to both applicants and applications, so the auto-resolve
    # must fail loudly instead of silently picking one.
    spec = {
        "base_table": "applicants",
        "joins": [
            {"table": "applications"},
            {"table": "staging"},
        ],
        "select": [{"table": "applicants", "field": "campus_id"}],
    }
    with pytest.raises(ValueError, match="Ambiguous join"):
        execute_query(spec, db_session)
