"""SQLAlchemy user repository."""
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.ports.user_repository import UserRepositoryPort
from app.infrastructure.db.mappers.user_mapper import to_domain, to_orm
from app.infrastructure.db.models.user import UserModel


class SQLAlchemyUserRepository(UserRepositoryPort):
    """SQLAlchemy implementation of UserRepositoryPort."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        orm_model = result.scalar_one_or_none()
        if not orm_model:
            return None
        return to_domain(orm_model)
    
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        orm_model = result.scalar_one_or_none()
        if not orm_model:
            return None
        return to_domain(orm_model)
    
    async def list_all(self) -> List[User]:
        """List all users."""
        result = await self.session.execute(select(UserModel))
        orm_models = result.scalars().all()
        return [to_domain(orm_model) for orm_model in orm_models]
    
    async def get_by_ids(self, user_ids: List[UUID]) -> List[User]:
        """Get multiple users by their IDs in a single query (optimizes N+1 queries)."""
        if not user_ids:
            return []
        result = await self.session.execute(
            select(UserModel).where(UserModel.id.in_(user_ids))
        )
        orm_models = result.scalars().all()
        return [to_domain(orm_model) for orm_model in orm_models]
    
    async def create(self, user: User) -> User:
        """Create a new user."""
        orm_model = to_orm(user)
        self.session.add(orm_model)
        await self.session.flush()
        await self.session.refresh(orm_model)
        return to_domain(orm_model)

