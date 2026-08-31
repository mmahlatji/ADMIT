from app.models.users import RoleEnum
from tests.test_notes_router import _make_actor, _make_client, _teardown
from tests.test_queries_system_logs import _create as create_log


def test_list_logs(db_session):
    create_log(db_session)
    actor = _make_actor(db_session, role=RoleEnum.admin, employee_id="8888888")

    client = _make_client(db_session, actor)
    try:
        res = client.get("/system_logs")
        assert res.status_code == 200
        assert len(res.json()) == 1
    finally:
        _teardown()


def test_list_logs_filter_by_entity_name(db_session):
    create_log(db_session)
    actor = _make_actor(db_session, role=RoleEnum.admin, employee_id="8888888")

    client = _make_client(db_session, actor)
    try:
        res = client.get("/system_logs", params={"entity_name": "applicant_marks"})
        assert res.status_code == 200
        assert len(res.json()) == 1
        res = client.get("/system_logs", params={"entity_name": "other"})
        assert res.json() == []
    finally:
        _teardown()


def test_list_logs_forbidden_for_committee(db_session):
    actor = _make_actor(db_session, role=RoleEnum.committee, employee_id="8888888")

    client = _make_client(db_session, actor)
    try:
        res = client.get("/system_logs")
        assert res.status_code == 403
    finally:
        _teardown()
