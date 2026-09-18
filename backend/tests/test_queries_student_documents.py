
from app.queries.student_documents import (
    create_student_document,
    delete_student_document,
    get_student_document_by_id,
    get_student_documents,
    get_student_documents_by_applicant,
    get_student_documents_by_hash,
    update_student_document,
)
from tests.test_queries_applicants import _create as create_applicant


def _create(db_session, sha256_hash="a" * 64):
    applicant = create_applicant(db_session)
    return create_student_document(
        db_session,
        applicant.applicant_id,
        "storage_key",
        "transcript.pdf",
        "application/pdf",
        sha256_hash,
    )


def test_create_and_get_student_document(db_session):
    document = _create(db_session)

    fetched = get_student_document_by_id(db_session, document.document_id)
    assert fetched is not None
    assert fetched.original_file_name == "transcript.pdf"


def test_get_student_documents_returns_all(db_session):
    applicant = create_applicant(db_session)
    create_student_document(
        db_session, applicant.applicant_id, "somekey", "a.pdf", "application/pdf", "a" * 64
    )
    create_student_document(
        db_session, applicant.applicant_id, "somekey", "b.pdf", "application/pdf", "b" * 64
    )

    assert len(get_student_documents(db_session)) == 2


def test_update_student_document_only_sets_passed_fields(db_session):
    document = _create(db_session)

    updated = update_student_document(db_session, document, original_file_name="renamed.pdf")
    assert updated.original_file_name == "renamed.pdf"
    assert updated.content_type == "application/pdf"


def test_delete_student_document(db_session):
    document = _create(db_session)

    delete_student_document(db_session, document)

    assert get_student_document_by_id(db_session, document.document_id) is None


def test_get_student_document_by_hash(db_session):
    document = _create(db_session, sha256_hash="a" * 64)
    applicant_id = document.applicant_id

    assert get_student_documents_by_hash(db_session, applicant_id, "a" * 64) is not None
    assert get_student_documents_by_hash(db_session, applicant_id, "b" * 64) is None


def test_get_student_document_by_hash_is_scoped_to_the_applicant(db_session):
    document = _create(db_session, sha256_hash="a" * 64)
    other = create_applicant(db_session, campus_id="cccddd002", employee_id="1000002")

    # Same bytes, different applicant: not a duplicate.
    assert get_student_documents_by_hash(db_session, other.applicant_id, "a" * 64) is None
    assert (
        get_student_documents_by_hash(db_session, document.applicant_id, "a" * 64) is not None
    )


def test_get_student_documents_by_applicant_is_scoped(db_session):
    applicant = create_applicant(db_session)
    other = create_applicant(db_session, campus_id="zzzyyy002", employee_id="7777777")
    create_student_document(
        db_session, applicant.applicant_id, "key-a", "mine.pdf", "application/pdf", "a" * 64
    )
    create_student_document(
        db_session, other.applicant_id, "key-b", "theirs.pdf", "application/pdf", "b" * 64
    )

    found = get_student_documents_by_applicant(db_session, applicant.applicant_id)
    assert [d.original_file_name for d in found] == ["mine.pdf"]


def test_get_student_documents_by_applicant_empty(db_session):
    applicant = create_applicant(db_session)

    assert get_student_documents_by_applicant(db_session, applicant.applicant_id) == []
