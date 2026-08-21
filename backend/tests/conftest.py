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
