"""SQLAlchemy question repository."""
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.question import Question
from app.domain.ports.question_repository import QuestionRepositoryPort
from app.infrastructure.db.mappers.question_mapper import to_domain, to_orm
from app.infrastructure.db.models.question import QuestionModel


class SQLAlchemyQuestionRepository(QuestionRepositoryPort):
    """SQLAlchemy implementation of QuestionRepositoryPort."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, question_id: UUID) -> Question | None:
        """Get question by ID."""
        result = await self.session.execute(
            select(QuestionModel).where(QuestionModel.id == question_id)
        )
        orm_model = result.scalar_one_or_none()
        if not orm_model:
            return None
        return to_domain(orm_model)
    
    async def list_all(self) -> List[Question]:
        """List all questions."""
        result = await self.session.execute(select(QuestionModel))
        orm_models = result.scalars().all()
        return [to_domain(orm_model) for orm_model in orm_models]
    
    async def create(self, question: Question) -> Question:
        """Create a new question."""
        orm_model = to_orm(question)
        self.session.add(orm_model)
        await self.session.flush()
        await self.session.refresh(orm_model)
        return to_domain(orm_model)

