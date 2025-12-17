"""SQLAlchemy option repository."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.option import Option
from app.domain.ports.option_repository import OptionRepositoryPort
from app.infrastructure.db.mappers.option_mapper import to_domain
from app.infrastructure.db.models.option import OptionModel


class SQLAlchemyOptionRepository(OptionRepositoryPort):
    """SQLAlchemy implementation of OptionRepositoryPort."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_question_id(self, question_id: UUID) -> list[Option]:
        """List all options for a question."""
        result = await self.session.execute(
            select(OptionModel).where(OptionModel.question_id == question_id)
        )
        orm_models = result.scalars().all()
        return [to_domain(orm_model) for orm_model in orm_models]

