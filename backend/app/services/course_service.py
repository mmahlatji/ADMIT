
import uuid

from app.models.courses import Course
from app.queries.course_repository import CourseRepository
from app.schemas.courses import CourseCreate


class CourseService:
    def __init__(self, course_repository: CourseRepository) -> None:
        self.repository = course_repository

    def get_by_id(self, course_id: uuid.UUID) -> Course | None:
        return self.repository.get_by_id(course_id)

    def get_all(self) -> list[Course]:
        return list(self.repository.get_all())

    def add(self, data: CourseCreate) -> None:
        course = Course(**data.model_dump())
        self.repository.add(course)
