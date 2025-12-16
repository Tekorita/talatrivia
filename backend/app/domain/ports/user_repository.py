"""User repository port."""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from app.domain.entities.user import User


class UserRepositoryPort(ABC):
    """Port for user repository operations."""
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            User entity or None if not found
        """
        pass

