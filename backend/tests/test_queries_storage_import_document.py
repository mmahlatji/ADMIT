from app.queries.storage import bucket as storage


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
    def __init__(self, name, bucket):
        self.name = name
        self.bucket = bucket

    def from_(self, name):
        assert name == self.name
        return self.bucket


class _FakeClient:
    def __init__(self, name, bucket):
        self.storage = _FakeStorage(name, bucket)


def test_upload_file_targets_bucket_and_uploads(monkeypatch):
    bucket = _FakeBucket()
    monkeypatch.setattr(storage, "get_supabase_client", lambda: _FakeClient("student_documents", bucket))

    path = storage.upload_file("student_documents", b"data", "application/pdf", "abc/def.pdf")

    assert path == "abc/def.pdf"
    assert len(bucket.uploads) == 1
    upload_path, content, options = bucket.uploads[0]
    assert upload_path == "abc/def.pdf"
    assert content == b"data"
    assert options == {"content-type": "application/pdf", "upsert": "false"}


def test_delete_file_removes_key(monkeypatch):
    bucket = _FakeBucket()
    monkeypatch.setattr(storage, "get_supabase_client", lambda: _FakeClient("student_documents", bucket))

    storage.delete_file("student_documents", "abc/def.pdf")

    assert bucket.removals == [["abc/def.pdf"]]


def test_generate_signed_url(monkeypatch):
    bucket = _FakeBucket()
    monkeypatch.setattr(storage, "get_supabase_client", lambda: _FakeClient("student_documents", bucket))

    url = storage.generate_signed_url("student_documents", "abc/def.pdf", 300)

    assert url == "https://example.com/abc/def.pdf"
    assert bucket.signed_urls == [("abc/def.pdf", 300)]
