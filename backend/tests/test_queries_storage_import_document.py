from app.models.import_runs import SourceType
from app.queries.storage import import_document as storage


class _FakeBucket:
    def __init__(self):
        self.uploads = []
        self.removals = []
        self.signed_urls = []

    def upload(self, path, file, file_options):
        self.uploads.append((path, file, file_options))

    def remove(self, keys):
        self.removals.append(keys)

    def create_signed_url(self, path, expires_in):
        self.signed_urls.append((path, expires_in))
        return {"signedURL": f"https://example.com/{path}"}


class _FakeStorage:
    def __init__(self, bucket):
        self.bucket = bucket

    def from_(self, name):
        assert name == "import_documents"
        return self.bucket


class _FakeClient:
    def __init__(self, bucket):
        self.storage = _FakeStorage(bucket)


def test_upload_documents_builds_path_and_uploads(monkeypatch):
    bucket = _FakeBucket()
    monkeypatch.setattr(storage, "get_supabase_client", lambda: _FakeClient(bucket))

    path = storage.upload_documents(b"data", "application/vnd.ms-excel", ".xlsx", SourceType.ASR)

    assert path.startswith("asr/")
    assert path.endswith(".xlsx")
    assert len(bucket.uploads) == 1
    upload_path, content, options = bucket.uploads[0]
    assert upload_path == path
    assert content == b"data"
    assert options == {"content-type": "application/vnd.ms-excel", "upsert": "false"}


def test_delete_document_removes_key(monkeypatch):
    bucket = _FakeBucket()
    monkeypatch.setattr(storage, "get_supabase_client", lambda: _FakeClient(bucket))

    storage.delete_document("asr/abc.xlsx")

    assert bucket.removals == [["asr/abc.xlsx"]]


def test_generate_signed_url(monkeypatch):
    bucket = _FakeBucket()
    monkeypatch.setattr(storage, "get_supabase_client", lambda: _FakeClient(bucket))

    url = storage.generate_signed_url("import_documents/asr/abc.xlsx")

    assert url == "https://example.com/import_documents/asr/abc.xlsx"
    assert bucket.signed_urls == [("import_documents/asr/abc.xlsx", 300)]
