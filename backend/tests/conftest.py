import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.users import User


@pytest.fixture()
def db_session():
    # StaticPool + check_same_thread=False: TestClient runs the app in a
    # worker thread, so the in-memory DB needs one shared connection.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Only creating the users table here, not the full Base.metadata: some of
    # the other models use Postgres-only types (e.g. JSONB) that SQLite can't
    # compile, and these tests don't touch those tables anyway.
    User.__table__.create(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


@pytest.fixture()
def make_token(rsa_keypair):
    private_key, _ = rsa_keypair

    def _make(
        sub: str | None = None,
        email: str = "student@uct.ac.za",
        expired: bool = False,
        first_name: str | None = "Test",
        last_name: str | None = "User",
    ):
        now = datetime.now(UTC)
        claims = {
            "sub": sub or str(uuid.uuid4()),
            "email": email,
            "aud": "authenticated",
            "exp": now - timedelta(minutes=5) if expired else now + timedelta(hours=1),
        }
        if first_name is not None and last_name is not None:
            claims["user_metadata"] = {"first_name": first_name, "last_name": last_name}
        return jwt.encode(claims, private_key, algorithm="RS256")

    return _make
