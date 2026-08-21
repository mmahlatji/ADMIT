
import uuid

from app.models.academic_programs import AcademicProgram
from app.queries.academic_program_repository import AcademicProgramRepository
from app.schemas.academic_programs import AcademicProgramCreate


class AcademicProgramService:
    def __init__(self, academic_program_repository: AcademicProgramRepository) -> None:
        self.repository = academic_program_repository

    def get_by_id(self, academic_program_id: uuid.UUID) -> AcademicProgram | None:
        return self.repository.get_by_id(academic_program_id)

    def get_all(self) -> list[AcademicProgram]:
        return list(self.repository.get_all())

    def add(self, data: AcademicProgramCreate) -> None:
        academic_program = AcademicProgram(**data.model_dump())
        self.repository.add(academic_program)
