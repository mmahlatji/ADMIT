from app.queries.motivations import (
    create_motivation,
    delete_motivation,
    get_motivation_by_id,
    get_motivations,
    update_motivation,
)
from tests.test_queries_applicants import _create as create_applicant


def test_create_and_get_motivation(db_session):
    create_applicant(db_session)
    motivation = create_motivation(db_session, "xxxyyy001", "Smith", "Noah", "Some text")

    fetched = get_motivation_by_id(db_session, motivation.motivation_id)
    assert fetched is not None
    assert fetched.motivation == "Some text"


def test_motivation_text_is_optional(db_session):
    create_applicant(db_session)
    motivation = create_motivation(db_session, "xxxyyy001", "Smith", "Noah")

    fetched = get_motivation_by_id(db_session, motivation.motivation_id)
    assert fetched.motivation is None


def test_get_motivations_returns_all(db_session):
    create_applicant(db_session, "xxxyyy001", "1000001")
    create_applicant(db_session, "xxxyyy002", "1000002")
    create_motivation(db_session, "xxxyyy001", "Smith", "Noah")
    create_motivation(db_session, "xxxyyy002", "Doe", "Jane")

    assert len(get_motivations(db_session)) == 2


def test_update_motivation_only_sets_passed_fields(db_session):
    create_applicant(db_session)
    motivation = create_motivation(db_session, "xxxyyy001", "Smith", "Noah")

    updated = update_motivation(db_session, motivation, motivation="New text")
    assert updated.last_name == "Smith"
    assert updated.motivation == "New text"


def test_delete_motivation(db_session):
    create_applicant(db_session)
    motivation = create_motivation(db_session, "xxxyyy001", "Smith", "Noah")

    delete_motivation(db_session, motivation)

    assert get_motivation_by_id(db_session, motivation.motivation_id) is None
