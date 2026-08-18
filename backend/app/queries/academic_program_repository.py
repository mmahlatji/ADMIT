
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic_programs import AcademicProgram


class AcademicProgramRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, academic_program_id: int) -> AcademicProgram | None:
        return self.session.get(AcademicProgram, academic_program_id)

    def get_all(self) -> list[AcademicProgram]:
        return list(self.session.scalars(select(AcademicProgram)).all())

    def add(self, academic_program: AcademicProgram) -> None:
        self.session.add(academic_program)
        self.session.commit()
