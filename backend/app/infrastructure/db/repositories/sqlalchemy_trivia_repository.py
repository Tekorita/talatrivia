"""SQLAlchemy trivia repository."""
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.entities.trivia import Trivia
from app.domain.ports.trivia_repository import TriviaRepositoryPort
from app.infrastructure.db.models.trivia import TriviaModel
from app.infrastructure.db.mappers.trivia_mapper import to_domain


class SQLAlchemyTriviaRepository(TriviaRepositoryPort):
    """SQLAlchemy implementation of TriviaRepositoryPort."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, trivia_id: UUID) -> Optional[Trivia]:
        """Get trivia by ID."""
        result = await self.session.execute(
            select(TriviaModel).where(TriviaModel.id == trivia_id)
        )
        orm_model = result.scalar_one_or_none()
        if not orm_model:
            return None
        return to_domain(orm_model)
    
    async def update(self, trivia: Trivia) -> None:
        """Update trivia."""
        result = await self.session.execute(
            select(TriviaModel).where(TriviaModel.id == trivia.id)
        )
        orm_model = result.scalar_one()
        
        # Update fields
        orm_model.title = trivia.title
        orm_model.description = trivia.description
        orm_model.topic = trivia.topic
        orm_model.status = trivia.status.value
        orm_model.current_question_index = trivia.current_question_index
        orm_model.question_started_at = trivia.question_started_at
        orm_model.started_at = trivia.started_at
        orm_model.finished_at = trivia.finished_at
        
        await self.session.commit()

