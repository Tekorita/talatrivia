"""Trivia repository port."""
from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.trivia import Trivia


class TriviaRepositoryPort(ABC):
    """Port for trivia repository operations."""
    
    @abstractmethod
    async def get_by_id(self, trivia_id: UUID) -> Trivia | None:
        """
        Get trivia by ID.
        
        Args:
            trivia_id: The trivia ID
            
        Returns:
            Trivia entity or None if not found
        """
        pass
    
    @abstractmethod
    async def update(self, trivia: Trivia) -> None:
        """
        Update trivia.
        
        Args:
            trivia: The trivia entity to update
        """
        pass

