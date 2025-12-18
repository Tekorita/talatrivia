"""SQLAlchemy trivia repository."""
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.trivia import Trivia
from app.domain.ports.trivia_repository import TriviaRepositoryPort
from app.infrastructure.db.mappers.trivia_mapper import _to_naive_dt, to_domain, to_orm
from app.infrastructure.db.models.trivia import TriviaModel


class SQLAlchemyTriviaRepository(TriviaRepositoryPort):
    """SQLAlchemy implementation of TriviaRepositoryPort."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, trivia_id: UUID) -> Trivia | None:
        """Get trivia by ID."""
        result = await self.session.execute(
            select(TriviaModel).where(TriviaModel.id == trivia_id)
        )
        orm_model = result.scalar_one_or_none()
        if not orm_model:
            return None
        return to_domain(orm_model)
    
    async def list_all(self) -> List[Trivia]:
        """List all trivias."""
        result = await self.session.execute(select(TriviaModel))
        orm_models = result.scalars().all()
        return [to_domain(orm_model) for orm_model in orm_models]
    
    async def create(self, trivia: Trivia) -> Trivia:
        """Create a new trivia."""
        orm_model = to_orm(trivia)
        self.session.add(orm_model)
        await self.session.flush()
        await self.session.refresh(orm_model)
        return to_domain(orm_model)
    
    async def update(self, trivia: Trivia) -> None:
        """Update trivia."""
        result = await self.session.execute(
            select(TriviaModel).where(TriviaModel.id == trivia.id)
        )
        orm_model = result.scalar_one()
        
        # Update fields (convert timezone-aware datetimes to naive)
        orm_model.title = trivia.title
        orm_model.description = trivia.description
        orm_model.topic = trivia.topic
        orm_model.status = trivia.status.value
        orm_model.current_question_index = trivia.current_question_index
        orm_model.question_started_at = _to_naive_dt(trivia.question_started_at)
        orm_model.started_at = _to_naive_dt(trivia.started_at)
        orm_model.finished_at = _to_naive_dt(trivia.finished_at)
        
        await self.session.commit()

