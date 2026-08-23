import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.deps import get_current_user


class _FakeSigningKey:
    def __init__(self, key):
        self.key = key


class _FakeJWKClient:
    def __init__(self, key):
        self._key = key

    def get_signing_key_from_jwt(self, token):
        return _FakeSigningKey(self._key)


def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_get_current_user_creates_row_for_new_login(db_session, rsa_keypair, make_token, monkeypatch):
    _, public_key = rsa_keypair
    monkeypatch.setattr("app.deps.get_jwks_client", lambda: _FakeJWKClient(public_key))

    user_id = uuid.uuid4()
    token = make_token(sub=str(user_id), email="convenor@uct.ac.za", first_name="Jan", last_name="B")

    user = get_current_user(_creds(token), db_session)
    assert user.id == user_id
    assert user.role is None
    assert user.first_name == "Jan"


def test_get_current_user_allows_missing_name_metadata(
    db_session, rsa_keypair, make_token, monkeypatch
):
    _, public_key = rsa_keypair
    monkeypatch.setattr("app.deps.get_jwks_client", lambda: _FakeJWKClient(public_key))

    token = make_token(first_name=None, last_name=None)

    user = get_current_user(_creds(token), db_session)
    assert user.first_name is None


def test_get_current_user_rejects_bad_domain(db_session, rsa_keypair, make_token, monkeypatch):
    _, public_key = rsa_keypair
    monkeypatch.setattr("app.deps.get_jwks_client", lambda: _FakeJWKClient(public_key))

    token = make_token(email="outsider@gmail.com")

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(_creds(token), db_session)
    assert exc_info.value.status_code == 403


def test_get_current_user_rejects_bad_signature(db_session, rsa_keypair, make_token, monkeypatch):
    wrong_public_key = rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key()
    monkeypatch.setattr("app.deps.get_jwks_client", lambda: _FakeJWKClient(wrong_public_key))

    token = make_token()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(_creds(token), db_session)
    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_expired_token(db_session, rsa_keypair, make_token, monkeypatch):
    _, public_key = rsa_keypair
    monkeypatch.setattr("app.deps.get_jwks_client", lambda: _FakeJWKClient(public_key))

    token = make_token(expired=True)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(_creds(token), db_session)
    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_malformed_token(db_session, rsa_keypair, monkeypatch):
    _, public_key = rsa_keypair
    monkeypatch.setattr("app.deps.get_jwks_client", lambda: _FakeJWKClient(public_key))

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(_creds("not-a-jwt"), db_session)
    assert exc_info.value.status_code == 401
