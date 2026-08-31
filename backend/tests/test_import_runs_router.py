from app.models.users import RoleEnum
from tests.test_notes_router import _make_actor, _make_client, _teardown
from tests.test_queries_import_runs import _create as create_import_run


def test_list_import_runs(db_session):
    create_import_run(db_session)
    actor = _make_actor(db_session, role=RoleEnum.admin, employee_id="8888888")

    client = _make_client(db_session, actor)
    try:
        res = client.get("/import_runs")
        assert res.status_code == 200
        assert len(res.json()) == 1
    finally:
        _teardown()


def test_get_import_run(db_session):
    import_run = create_import_run(db_session)
    actor = _make_actor(db_session, role=RoleEnum.admin, employee_id="8888888")

    client = _make_client(db_session, actor)
    try:
        res = client.get(f"/import_runs/{import_run.import_run_id}")
        assert res.status_code == 200
        assert res.json()["file_name"] == "asr.xlsx"
    finally:
        _teardown()


def test_list_import_runs_forbidden_for_committee(db_session):
    actor = _make_actor(db_session, role=RoleEnum.committee, employee_id="8888888")

    client = _make_client(db_session, actor)
    try:
        res = client.get("/import_runs")
        assert res.status_code == 403
    finally:
        _teardown()
