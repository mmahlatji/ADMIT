import uuid

from app.queries.student_documents import (
    create_student_document,
    delete_student_document,
    get_student_document_by_id,
    get_student_documents,
    update_student_document,
)
from tests.test_queries_applicants import _create as create_applicant


def _create(db_session, sha256_hash="a" * 64):
    applicant = create_applicant(db_session)
    return create_student_document(
        db_session,
        applicant.applicant_id,
        uuid.uuid4(),
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
        db_session, applicant.applicant_id, uuid.uuid4(), "a.pdf", "application/pdf", "a" * 64
    )
    create_student_document(
        db_session, applicant.applicant_id, uuid.uuid4(), "b.pdf", "application/pdf", "b" * 64
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
