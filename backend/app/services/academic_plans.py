from sqlalchemy.orm import Session

from app.queries import academic_plans as acad_queries


def get_academic_plans_by_department_code(db: Session, department_code: str):
    return acad_queries.get_academic_plans_by_department_code(db, department_code)