from app.queries.storage import supabase as supabase_module


def test_get_supabase_client_is_cached(monkeypatch):
    calls = []

    def fake_create(url, key):
        calls.append((url, key))
        return object()

    monkeypatch.setattr(supabase_module, "create_client", fake_create)
    supabase_module.get_supabase_client.cache_clear()

    first = supabase_module.get_supabase_client()
    second = supabase_module.get_supabase_client()

    assert first is second
    assert len(calls) == 1
