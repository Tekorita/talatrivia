"""SQLAlchemy participation repository."""
from typing import List
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.participation import Participation
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.infrastructure.db.mappers.participation_mapper import _to_naive_dt, to_domain
from app.infrastructure.db.models.answer import AnswerModel
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
            joined_at=_to_naive_dt(participation.joined_at),
            ready_at=_to_naive_dt(participation.ready_at),
            finished_at=_to_naive_dt(participation.finished_at),
            last_seen_at=_to_naive_dt(participation.last_seen_at),
            fifty_fifty_used=participation.fifty_fifty_used,
            fifty_fifty_question_id=participation.fifty_fifty_question_id,
        )
        self.session.add(orm_model)
        await self.session.commit()
        await self.session.refresh(orm_model)
        return to_domain(orm_model)
    
    async def update(self, participation: Participation) -> None:
        """Update participation."""
        import logging
        logger = logging.getLogger(__name__)

        orm_model = await self.session.get(ParticipationModel, participation.id)
        if not orm_model:
            logger.warning("Participation not found for update: %s", participation.id)
            return

        orm_model.status = participation.status.value
        orm_model.score = participation.score
        orm_model.joined_at = _to_naive_dt(participation.joined_at)
        orm_model.ready_at = _to_naive_dt(participation.ready_at)
        orm_model.finished_at = _to_naive_dt(participation.finished_at)
        orm_model.last_seen_at = _to_naive_dt(participation.last_seen_at)
        orm_model.fifty_fifty_used = participation.fifty_fifty_used
        orm_model.fifty_fifty_question_id = participation.fifty_fifty_question_id

        await self.session.commit()
        logger.info(
            "Updated participation %s score=%s",
            participation.id,
            participation.score,
        )
    
    async def list_by_trivia(self, trivia_id: UUID) -> List[Participation]:
        """List all participations for a trivia, ordered by score DESC."""
        result = await self.session.execute(
            select(ParticipationModel)
            .where(ParticipationModel.trivia_id == trivia_id)
            .order_by(ParticipationModel.score.desc())
        )
        orm_models = result.scalars().all()
        return [to_domain(orm_model) for orm_model in orm_models]
    
    async def list_by_user(self, user_id: UUID) -> List[Participation]:
        """List all participations for a user."""
        result = await self.session.execute(
            select(ParticipationModel)
            .where(ParticipationModel.user_id == user_id)
        )
        orm_models = result.scalars().all()
        return [to_domain(orm_model) for orm_model in orm_models]

    async def recompute_score(self, trivia_id: UUID, user_id: UUID) -> int:
        """Recompute and persist score for a single participation."""
        subquery = (
            select(func.coalesce(func.sum(AnswerModel.earned_points), 0))
            .where(AnswerModel.participation_id == ParticipationModel.id)
            .correlate(ParticipationModel)
        )

        stmt = (
            update(ParticipationModel)
            .where(
                ParticipationModel.trivia_id == trivia_id,
                ParticipationModel.user_id == user_id,
            )
            .values(score=subquery.scalar_subquery())
            .returning(ParticipationModel.score)
        )

        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none() or 0

    async def recompute_scores_for_trivia(self, trivia_id: UUID) -> None:
        """Recompute and persist scores for all participations of a trivia."""
        subquery = (
            select(func.coalesce(func.sum(AnswerModel.earned_points), 0))
            .where(AnswerModel.participation_id == ParticipationModel.id)
            .correlate(ParticipationModel)
        )

        stmt = (
            update(ParticipationModel)
            .where(ParticipationModel.trivia_id == trivia_id)
            .values(score=subquery.scalar_subquery())
        )

        await self.session.execute(stmt)
        await self.session.commit()

