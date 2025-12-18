"""Question repository port."""
from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.domain.entities.question import Question


class QuestionRepositoryPort(ABC):
    """Port for question repository operations."""

    @abstractmethod
    async def get_by_id(self, question_id: UUID) -> Question | None:
        """
        Get question by ID.

        Args:
            question_id: The question ID

        Returns:
            Question entity or None if not found
        """
        pass
    
    @abstractmethod
    async def list_all(self) -> List[Question]:
        """
        List all questions.
        
        Returns:
            List of all question entities
        """
        pass
    
    @abstractmethod
    async def create(self, question: Question) -> Question:
        """
        Create a new question.
        
        Args:
            question: The question entity to create
            
        Returns:
            The created question entity
        """
        pass

