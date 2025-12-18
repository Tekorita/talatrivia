"""Participation repository port."""
from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.domain.entities.participation import Participation


class ParticipationRepositoryPort(ABC):
    """Port for participation repository operations."""
    
    @abstractmethod
    async def get_by_trivia_and_user(
        self, 
        trivia_id: UUID, 
        user_id: UUID
    ) -> Participation | None:
        """
        Get participation by trivia and user.
        
        Args:
            trivia_id: The trivia ID
            user_id: The user ID
            
        Returns:
            Participation entity or None if not found
        """
        pass
    
    @abstractmethod
    async def create(self, participation: Participation) -> Participation:
        """
        Create a new participation.
        
        Args:
            participation: The participation entity to create
            
        Returns:
            The created participation
        """
        pass
    
    @abstractmethod
    async def update(self, participation: Participation) -> None:
        """
        Update participation.
        
        Args:
            participation: The participation entity to update
        """
        pass

    @abstractmethod
    async def recompute_score(self, trivia_id: UUID, user_id: UUID) -> int:
        """
        Recompute and persist score for a user's participation in a trivia
        based on the sum of earned_points in answers. Returns the new score.
        """
        pass

    @abstractmethod
    async def recompute_scores_for_trivia(self, trivia_id: UUID) -> None:
        """
        Recompute and persist scores for all participations of a trivia
        based on the sum of earned_points in answers.
        """
        pass
    
    @abstractmethod
    async def list_by_trivia(self, trivia_id: UUID) -> List[Participation]:
        """
        List all participations for a trivia.
        
        Args:
            trivia_id: The trivia ID
            
        Returns:
            List of participation entities
        """
        pass
    
    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> List[Participation]:
        """
        List all participations for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            List of participation entities
        """
        pass

