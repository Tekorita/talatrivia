"""SQLAlchemy question repository."""
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.entities.question import Question
from app.domain.ports.question_repository import QuestionRepositoryPort
from app.infrastructure.db.models.question import QuestionModel
from app.infrastructure.db.mappers.question_mapper import to_domain


class SQLAlchemyQuestionRepository(QuestionRepositoryPort):
    """SQLAlchemy implementation of QuestionRepositoryPort."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, question_id: UUID) -> Optional[Question]:
        """Get question by ID."""
        result = await self.session.execute(
            select(QuestionModel).where(QuestionModel.id == question_id)
        )
        orm_model = result.scalar_one_or_none()
        if not orm_model:
            return None
        return to_domain(orm_model)

