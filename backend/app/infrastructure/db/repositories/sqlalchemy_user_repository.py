"""SQLAlchemy user repository."""
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.entities.user import User
from app.domain.ports.user_repository import UserRepositoryPort
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.mappers.user_mapper import to_domain


class SQLAlchemyUserRepository(UserRepositoryPort):
    """SQLAlchemy implementation of UserRepositoryPort."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        orm_model = result.scalar_one_or_none()
        if not orm_model:
            return None
        return to_domain(orm_model)

