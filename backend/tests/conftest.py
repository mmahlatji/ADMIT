import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base


@pytest.fixture()
def db_session():
    # StaticPool + check_same_thread=False: TestClient runs the app in a
    # worker thread, so the in-memory DB needs one shared connection.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # used to only create the users table since staging/system_logs had postgres-only
    # JSONB columns SQLite couldn't compile, now that they're plain JSON this covers everything
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


# sentinel so "generate one" is distinguishable from "deliberately omit it"
_AUTO_EMPLOYEE_ID = object()


@pytest.fixture()
def make_token(rsa_keypair):
    private_key, _ = rsa_keypair

    def _make(
        sub: str | None = None,
        email: str = "student@uct.ac.za",
        expired: bool = False,
        first_name: str | None = "Test",
        last_name: str | None = "User",
        employee_id: str | None = _AUTO_EMPLOYEE_ID,
    ):
        now = datetime.now(UTC)
        claims = {
            "sub": sub or str(uuid.uuid4()),
            "email": email,
            "aud": "authenticated",
            "exp": now - timedelta(minutes=5) if expired else now + timedelta(hours=1),
        }
        # employee_id is collected at signup, so a real token always carries one:
        # default to a unique generated id, and pass employee_id=None to build
        # the odd token that deliberately lacks it.
        if employee_id is _AUTO_EMPLOYEE_ID:
            employee_id = str(uuid.uuid4().int)[:7]
        metadata = {}
        if employee_id is not None:
            metadata["employee_id"] = employee_id
        if first_name is not None and last_name is not None:
            metadata.update({"first_name": first_name, "last_name": last_name})
        if metadata:
            claims["user_metadata"] = metadata
        return jwt.encode(claims, private_key, algorithm="RS256")

    return _make
