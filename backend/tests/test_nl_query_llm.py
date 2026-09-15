import asyncio
import json
import uuid

import httpx
import pytest

from app.llm import prompts
from app.llm.client import OllamaLLMClient
from app.llm.exceptions import LLMResponseError, LLMUnavailableError
from app.models.users import RoleEnum
from app.queries.departments import create_department
from app.services import nl_query as nl_query_service
from app.services.nl_query import describe_schema
from tests.test_notes_router import _make_actor, _make_client, _teardown


class MockLLMClient:
    """Deterministic client: returns a canned spec."""

    def __init__(self, spec: dict | None = None) -> None:
        self._spec = spec if spec is not None else {"base_table": "departments", "action": "count"}

    async def parse_intent(self, prompt: str, schema: dict) -> dict:
        return self._spec


# ---- prompt building ----


def test_system_prompt_contains_schema_and_contract():
    prompt = prompts.build_system_prompt(describe_schema(RoleEnum.convenor))
    assert "departments" in prompt
    assert "base_table" in prompt
    assert "count" in prompt
    assert "eq, neq, gt, gte, lt, lte, in, like" in prompt


# ---- JSON extraction ----


def test_extract_json_plain():
    assert prompts._extract_json('{"a": 1}') == '{"a": 1}'


def test_extract_json_fenced():
    assert prompts._extract_json('```json\n{"a": 1}\n```') == '{"a": 1}'


def test_extract_json_embedded():
    assert prompts._extract_json('Here: {"a": {"b": 2}} done') == '{"a": {"b": 2}}'


def test_extract_json_no_object_raises():
    with pytest.raises(ValueError, match="No JSON object"):
        prompts._extract_json("no json here")


# ---- Ollama client ----


def _client(handler) -> OllamaLLMClient:
    return OllamaLLMClient(
        "http://localhost:11434", "test-model", 10.0, transport=httpx.MockTransport(handler)
    )


def test_ollama_parse_intent_uses_json_mode():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200, json={"message": {"content": '{"base_table": "applicants", "action": "count"}'}}
        )

    spec = asyncio.run(
        _client(handler).parse_intent("how many applicants?", describe_schema(RoleEnum.convenor))
    )

    assert captured["payload"]["format"] == "json"
    assert captured["payload"]["model"] == "test-model"
    assert captured["payload"]["stream"] is False
    assert spec == {"base_table": "applicants", "action": "count"}


def test_ollama_parse_intent_strips_fences():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"message": {"content": '```json\n{"base_table": "departments", "action": "count"}\n```'}},
        )

    assert asyncio.run(_client(handler).parse_intent("x", describe_schema(RoleEnum.convenor))) == {
        "base_table": "departments",
        "action": "count",
    }


def test_ollama_parse_intent_bad_json_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": "definitely not json"}})

    with pytest.raises(LLMResponseError):
        asyncio.run(_client(handler).parse_intent("x", describe_schema(RoleEnum.convenor)))


def test_ollama_parse_intent_non_dict_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": "[1, 2, 3]"}})

    with pytest.raises(LLMResponseError):
        asyncio.run(_client(handler).parse_intent("x", describe_schema(RoleEnum.convenor)))


def test_ollama_unavailable_on_non_200():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "model not loaded"})

    with pytest.raises(LLMUnavailableError):
        asyncio.run(_client(handler).parse_intent("x", describe_schema(RoleEnum.convenor)))


def test_ollama_unavailable_on_connect_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    with pytest.raises(LLMUnavailableError):
        asyncio.run(_client(handler).parse_intent("x", describe_schema(RoleEnum.convenor)))


# ---- mock client + saved-query end-to-end ----


@pytest.mark.asyncio
async def test_ask_count_end_to_end_with_mock(db_session):
    create_department(db_session, "CSC", "Computer Science")
    create_department(db_session, "MAM", "Mathematics")
    db_session.commit()

    actor = _make_actor(db_session)
    mock = MockLLMClient(spec={"base_table": "departments", "action": "count"})
    out = await nl_query_service.ask("how many departments?", db_session, actor, llm=mock)
    assert out["rows"] == 2
    assert "query_id" in out


@pytest.mark.asyncio
async def test_ask_persists_saved_query(db_session):
    create_department(db_session, "CSC")
    db_session.commit()

    actor = _make_actor(db_session)
    out = await nl_query_service.ask("how many departments?", db_session, actor, llm=MockLLMClient())

    saved = nl_query_service.list_queries(db_session, actor)
    assert len(saved) == 1
    assert saved[0].query_id == out["query_id"]
    assert saved[0].prompt == "how many departments?"


@pytest.mark.asyncio
async def test_ask_stores_llm_title(db_session):
    create_department(db_session, "CSC")
    db_session.commit()

    actor = _make_actor(db_session)
    mock = MockLLMClient(
        spec={"title": "Department count", "base_table": "departments", "action": "count"}
    )
    out = await nl_query_service.ask("how many departments?", db_session, actor, llm=mock)

    assert out["title"] == "Department count"
    saved = nl_query_service.list_queries(db_session, actor)
    assert saved[0].title == "Department count"
    assert "title" not in saved[0].spec  # title is popped before the spec is stored


@pytest.mark.asyncio
async def test_ask_title_falls_back_to_prompt(db_session):
    create_department(db_session, "CSC")
    db_session.commit()

    actor = _make_actor(db_session)
    out = await nl_query_service.ask("how many departments?", db_session, actor, llm=MockLLMClient())

    assert out["title"] == "how many departments?"
    saved = nl_query_service.list_queries(db_session, actor)
    assert saved[0].title == "how many departments?"


@pytest.mark.asyncio
async def test_ask_does_not_persist_on_invalid_query(db_session):
    create_department(db_session, "CSC")
    db_session.commit()

    actor = _make_actor(db_session)
    mock = MockLLMClient(spec={"base_table": "not_a_table", "action": "count"})
    with pytest.raises(ValueError):
        await nl_query_service.ask("boom", db_session, actor, llm=mock)
    assert nl_query_service.list_queries(db_session, actor) == []


@pytest.mark.asyncio
async def test_get_page_paginates_by_skip_and_limit(db_session):
    create_department(db_session, "CSC", "Computer Science")
    create_department(db_session, "MAM", "Mathematics")
    create_department(db_session, "STA", "Statistics")
    db_session.commit()

    actor = _make_actor(db_session)
    mock = MockLLMClient(
        spec={
            "base_table": "departments",
            "select": [{"field": "department_code"}],
            "order_by": [{"field": "department_code", "direction": "asc"}],
        }
    )

    first = await nl_query_service.ask("list departments", db_session, actor, llm=mock)
    assert [r["department_code"] for r in first["rows"]] == ["CSC", "MAM", "STA"]

    second = nl_query_service.get_page(first["query_id"], 1, 1, db_session, actor)
    assert [r["department_code"] for r in second] == ["MAM"]

    back = nl_query_service.get_page(first["query_id"], 0, 2, db_session, actor)
    assert [r["department_code"] for r in back] == ["CSC", "MAM"]


@pytest.mark.asyncio
async def test_delete_saved_query(db_session):
    create_department(db_session, "CSC")
    db_session.commit()

    actor = _make_actor(db_session)
    out = await nl_query_service.ask("how many departments?", db_session, actor, llm=MockLLMClient())

    nl_query_service.delete_query(db_session, actor, out["query_id"])
    assert nl_query_service.list_queries(db_session, actor) == []


def test_get_page_unknown_query_raises(db_session):
    actor = _make_actor(db_session)
    with pytest.raises(nl_query_service.SavedQueryNotFoundError):
        nl_query_service.get_page(uuid.uuid4(), 0, 10, db_session, actor)


@pytest.mark.asyncio
async def test_ask_committee_cannot_query_disallowed_table(db_session):
    actor = _make_actor(db_session, role=RoleEnum.committee)
    mock = MockLLMClient(spec={"base_table": "users", "action": "count"})
    with pytest.raises(ValueError, match="not available"):
        await nl_query_service.ask("count users", db_session, actor, llm=mock)


def test_endpoint_returns_200_with_mock(db_session, monkeypatch):
    create_department(db_session, "CSC")
    actor = _make_actor(db_session)

    monkeypatch.setattr(nl_query_service, "get_llm_client", lambda: MockLLMClient())

    client = _make_client(db_session, actor)
    try:
        res = client.post("/api/query", json={"prompt": "how many departments?"})
        assert res.status_code == 200
        body = res.json()
        assert body["rows"] == 1
        assert "query_id" in body
    finally:
        _teardown()


def test_endpoint_lists_saved_queries(db_session, monkeypatch):
    create_department(db_session, "CSC")
    actor = _make_actor(db_session)

    monkeypatch.setattr(nl_query_service, "get_llm_client", lambda: MockLLMClient())

    client = _make_client(db_session, actor)
    try:
        client.post("/api/query", json={"prompt": "how many departments?"})
        res = client.get("/api/query")
        assert res.status_code == 200
        body = res.json()
        assert len(body) == 1
        assert body[0]["prompt"] == "how many departments?"
    finally:
        _teardown()


def test_endpoint_page_and_delete(db_session, monkeypatch):
    create_department(db_session, "CSC")
    create_department(db_session, "MAM")
    actor = _make_actor(db_session)

    monkeypatch.setattr(
        nl_query_service,
        "get_llm_client",
        lambda: MockLLMClient(
            spec={
                "base_table": "departments",
                "select": [{"field": "department_code"}],
                "order_by": [{"field": "department_code", "direction": "asc"}],
            }
        ),
    )

    client = _make_client(db_session, actor)
    try:
        created = client.post("/api/query", json={"prompt": "list departments"}).json()
        query_id = created["query_id"]
        assert [r["department_code"] for r in created["rows"]] == ["CSC", "MAM"]

        page = client.get(f"/api/query/{query_id}", params={"skip": 1, "limit": 1}).json()
        assert [r["department_code"] for r in page] == ["MAM"]

        assert client.delete(f"/api/query/{query_id}").status_code == 204
        assert client.get(f"/api/query/{query_id}").status_code == 404
    finally:
        _teardown()


def test_endpoint_returns_503_when_llm_unavailable(db_session, monkeypatch):
    actor = _make_actor(db_session)

    class _Failing:
        async def parse_intent(self, prompt, schema):
            raise LLMUnavailableError("Could not reach Ollama")

    monkeypatch.setattr(nl_query_service, "get_llm_client", lambda: _Failing())

    client = _make_client(db_session, actor)
    try:
        res = client.post("/api/query", json={"prompt": "hi"})
        assert res.status_code == 503
    finally:
        _teardown()


# ---- pagination bounds and role reach ----


def test_page_rejects_limit_above_max(db_session, monkeypatch):
    """An unbounded limit let one request pull a whole table into memory."""
    create_department(db_session, "CSC")
    actor = _make_actor(db_session)
    monkeypatch.setattr(nl_query_service, "get_llm_client", lambda: MockLLMClient())

    client = _make_client(db_session, actor)
    try:
        query_id = client.post("/api/query", json={"prompt": "how many?"}).json()["query_id"]
        assert client.get(f"/api/query/{query_id}", params={"limit": 100_000}).status_code == 422
        assert client.get(f"/api/query/{query_id}", params={"limit": 0}).status_code == 422
        assert client.get(f"/api/query/{query_id}", params={"skip": -1}).status_code == 422
        assert client.get(f"/api/query/{query_id}", params={"limit": 500}).status_code == 200
    finally:
        _teardown()


def test_admin_may_query(db_session, monkeypatch):
    """allowed_tables_for_role has always treated admin as unrestricted, but the
    router left it out, so that branch could never run."""
    create_department(db_session, "CSC")
    actor = _make_actor(db_session, role=RoleEnum.admin)
    monkeypatch.setattr(nl_query_service, "get_llm_client", lambda: MockLLMClient())

    client = _make_client(db_session, actor)
    try:
        assert client.post("/api/query", json={"prompt": "how many?"}).status_code == 200
    finally:
        _teardown()
