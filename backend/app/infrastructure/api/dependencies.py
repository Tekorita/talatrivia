"""API dependencies."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db

__all__ = ["get_db"]

