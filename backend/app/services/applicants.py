from sqlalchemy.orm import Session

from app.queries import applicants as applicant_queries


def list_applicants(db: Session, skip: int = 0, limit: int = 100):
    return applicant_queries.get_applicants(db, skip, limit)


def get_applicant_by_campus_id(db: Session, campus_id: str):
    return applicant_queries.get_applicant_by_campus_id_with_relations(db, campus_id)
