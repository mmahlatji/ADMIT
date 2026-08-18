
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.courses import Course


class CourseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, course_id: int) -> Course | None:
        return self.session.get(Course, course_id)

    def get_all(self) -> list[Course]:
        return list(self.session.scalars(select(Course)).all())

    def add(self, course: Course) -> None:
        self.session.add(course)
        self.session.commit()

