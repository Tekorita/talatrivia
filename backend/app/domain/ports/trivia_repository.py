"""Trivia repository port."""
from abc import ABC, abstractmethod
from typing import List
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
    async def list_all(self) -> List[Trivia]:
        """
        List all trivias.
        
        Returns:
            List of all trivia entities
        """
        pass
    
    @abstractmethod
    async def create(self, trivia: Trivia) -> Trivia:
        """
        Create a new trivia.
        
        Args:
            trivia: The trivia entity to create
            
        Returns:
            The created trivia entity
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

