"""SQLAlchemy answer repository."""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.domain.entities.answer import Answer
from app.domain.errors import ConflictError
from app.domain.ports.answer_repository import AnswerRepositoryPort
from app.infrastructure.db.models.answer import AnswerModel
from app.infrastructure.db.mappers.answer_mapper import to_domain


class SQLAlchemyAnswerRepository(AnswerRepositoryPort):
    """SQLAlchemy implementation of AnswerRepositoryPort."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_participation_and_trivia_question(
        self, participation_id: UUID, trivia_question_id: UUID
    ) -> Answer | None:
        """Get answer by participation and trivia question."""
        result = await self.session.execute(
            select(AnswerModel).where(
                AnswerModel.participation_id == participation_id,
                AnswerModel.trivia_question_id == trivia_question_id,
            )
        )
        orm_model = result.scalar_one_or_none()
        if not orm_model:
            return None
        return to_domain(orm_model)

    async def create(self, answer: Answer) -> Answer:
        """Create a new answer."""
        orm_model = AnswerModel(
            id=answer.id,
            participation_id=answer.participation_id,
            trivia_question_id=answer.trivia_question_id,
            selected_option_id=answer.selected_option_id,
            is_correct=answer.is_correct,
            earned_points=answer.earned_points,
            answered_at=answer.answered_at,
        )
        self.session.add(orm_model)
        try:
            await self.session.commit()
            await self.session.refresh(orm_model)
            return to_domain(orm_model)
        except IntegrityError as e:
            await self.session.rollback()
            # Check if it's a unique constraint violation
            if "uq_participation_trivia_question" in str(e.orig) or "unique" in str(e.orig).lower():
                raise ConflictError("Answer already submitted for this question") from e
            raise

