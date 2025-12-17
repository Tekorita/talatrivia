"""SQLAlchemy trivia question repository."""
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.domain.entities.trivia_question import TriviaQuestion
from app.domain.ports.trivia_question_repository import TriviaQuestionRepositoryPort
from app.infrastructure.db.models.trivia_question import TriviaQuestionModel
from app.infrastructure.db.mappers.trivia_question_mapper import to_domain


class SQLAlchemyTriviaQuestionRepository(TriviaQuestionRepositoryPort):
    """SQLAlchemy implementation of TriviaQuestionRepositoryPort."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_trivia_and_order(
        self, trivia_id: UUID, order: int
    ) -> Optional[TriviaQuestion]:
        """Get trivia question by trivia ID and order/position."""
        result = await self.session.execute(
            select(TriviaQuestionModel).where(
                TriviaQuestionModel.trivia_id == trivia_id,
                TriviaQuestionModel.position == order,
            )
        )
        orm_model = result.scalar_one_or_none()
        if not orm_model:
            return None
        return to_domain(orm_model)

    async def count_by_trivia(self, trivia_id: UUID) -> int:
        """Count questions in a trivia."""
        result = await self.session.execute(
            select(func.count(TriviaQuestionModel.id)).where(
                TriviaQuestionModel.trivia_id == trivia_id
            )
        )
        return result.scalar() or 0

