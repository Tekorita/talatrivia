"""SQLAlchemy participation repository."""
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.participation import Participation
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.infrastructure.db.mappers.participation_mapper import to_domain
from app.infrastructure.db.models.participation import ParticipationModel


class SQLAlchemyParticipationRepository(ParticipationRepositoryPort):
    """SQLAlchemy implementation of ParticipationRepositoryPort."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_trivia_and_user(
        self, 
        trivia_id: UUID, 
        user_id: UUID
    ) -> Participation | None:
        """Get participation by trivia and user."""
        result = await self.session.execute(
            select(ParticipationModel).where(
                ParticipationModel.trivia_id == trivia_id,
                ParticipationModel.user_id == user_id,
            )
        )
        orm_model = result.scalar_one_or_none()
        if not orm_model:
            return None
        return to_domain(orm_model)
    
    async def create(self, participation: Participation) -> Participation:
        """Create a new participation."""
        orm_model = ParticipationModel(
            id=participation.id,
            trivia_id=participation.trivia_id,
            user_id=participation.user_id,
            status=participation.status.value,
            score=participation.score,
            joined_at=participation.joined_at,
            ready_at=participation.ready_at,
            finished_at=participation.finished_at,
        )
        self.session.add(orm_model)
        await self.session.commit()
        await self.session.refresh(orm_model)
        return to_domain(orm_model)
    
    async def update(self, participation: Participation) -> None:
        """Update participation."""
        result = await self.session.execute(
            select(ParticipationModel).where(ParticipationModel.id == participation.id)
        )
        orm_model = result.scalar_one()
        
        # Update fields
        orm_model.status = participation.status.value
        orm_model.score = participation.score
        orm_model.joined_at = participation.joined_at
        orm_model.ready_at = participation.ready_at
        orm_model.finished_at = participation.finished_at
        
        await self.session.commit()
    
    async def list_by_trivia(self, trivia_id: UUID) -> List[Participation]:
        """List all participations for a trivia."""
        result = await self.session.execute(
            select(ParticipationModel).where(
                ParticipationModel.trivia_id == trivia_id
            )
        )
        orm_models = result.scalars().all()
        return [to_domain(orm_model) for orm_model in orm_models]

