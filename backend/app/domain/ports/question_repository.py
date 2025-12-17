"""Question repository port."""
from abc import ABC, abstractmethod
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

