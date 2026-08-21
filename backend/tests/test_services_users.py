import uuid

import pytest

from app.models.user import RoleEnum
from app.services.users import (
    DomainNotAllowedError,
    assign_role,
    get_or_create_user,
    is_allowed_domain,
)


def _claims(email="convenor@uct.ac.za", first_name="A", last_name="B", sub=None):
    claims = {"sub": sub or str(uuid.uuid4()), "email": email}
    if first_name is not None:
        claims["user_metadata"] = {"first_name": first_name, "last_name": last_name}
    return claims


def test_is_allowed_domain():
    assert is_allowed_domain("student@uct.ac.za")
    assert is_allowed_domain("student@myuct.ac.za")
    assert is_allowed_domain("STUDENT@UCT.AC.ZA")
    assert not is_allowed_domain("student@gmail.com")


def test_get_or_create_user_creates_once(db_session):
    claims = _claims()
    user = get_or_create_user(db_session, claims)
    assert user.id == uuid.UUID(claims["sub"])
    assert user.role is None
    assert user.first_name == "A"

    same_user = get_or_create_user(db_session, claims)
    assert same_user.id == user.id


def test_get_or_create_user_rejects_bad_domain(db_session):
    with pytest.raises(DomainNotAllowedError):
        get_or_create_user(db_session, _claims(email="outsider@gmail.com"))


def test_get_or_create_user_allows_missing_name(db_session):
    claims = {"sub": str(uuid.uuid4()), "email": "noname@uct.ac.za"}
    user = get_or_create_user(db_session, claims)
    assert user.first_name is None
    assert user.last_name is None


def test_assign_role_grant_sets_approval_and_revoke_preserves_it(db_session):
    actor = get_or_create_user(db_session, _claims(email="convenor@uct.ac.za"))
    actor.employee_id = "1234567"
    actor.role = RoleEnum.convenor
    target = get_or_create_user(db_session, _claims(email="committee@uct.ac.za"))

    assign_role(db_session, actor, target, RoleEnum.committee)
    assert target.role == RoleEnum.committee
    assert target.approved_by == "1234567"
    approved_at = target.approved_at
    assert approved_at is not None

    assign_role(db_session, actor, target, None)
    assert target.role is None
    assert target.approved_by == "1234567"
    assert target.approved_at == approved_at


def test_assign_role_rejects_non_convenor_actor(db_session):
    actor = get_or_create_user(db_session, _claims(email="committee@uct.ac.za"))
    actor.role = RoleEnum.committee
    target = get_or_create_user(db_session, _claims(email="other@uct.ac.za"))

    with pytest.raises(PermissionError):
        assign_role(db_session, actor, target, RoleEnum.committee)
