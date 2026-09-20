from app.models.votes import VoteDecision
from app.queries.votes import create_vote, delete_vote, get_vote_by_id, get_votes, update_vote
from tests.test_queries_applications import _create as create_application
from tests.test_queries_notes import _create_author


def _create(db_session):
    create_application(db_session)
    _create_author(db_session)
    return create_vote(db_session, "00000001", "xxxyyy001", VoteDecision.YES, "9999999")


def test_create_and_get_vote(db_session):
    vote = _create(db_session)

    fetched = get_vote_by_id(db_session, vote.vote_id)
    assert fetched is not None
    assert fetched.vote == VoteDecision.YES


def test_get_votes_returns_all(db_session):
    create_application(db_session)
    _create_author(db_session)
    _create_author(db_session, employee_id="8888888", email="other@uct.ac.za")
    create_vote(db_session, "00000001", "xxxyyy001", VoteDecision.YES, "9999999")
    create_vote(db_session, "00000001", "xxxyyy001", VoteDecision.NO, "8888888")

    assert len(get_votes(db_session)) == 2


def test_update_vote_only_sets_passed_fields(db_session):
    vote = _create(db_session)

    updated = update_vote(db_session, vote, voter_id="8888888")
    assert updated.voter_id == "8888888"
    assert updated.application_number == "00000001"


def test_delete_vote(db_session):
    vote = _create(db_session)

    delete_vote(db_session, vote)

    assert get_vote_by_id(db_session, vote.vote_id) is None
