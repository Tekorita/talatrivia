"""TriviaQuestion repository port."""
from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.trivia_question import TriviaQuestion


class TriviaQuestionRepositoryPort(ABC):
    """Port for trivia question repository operations."""

    @abstractmethod
    async def get_by_trivia_and_order(
        self, trivia_id: UUID, order: int
    ) -> TriviaQuestion | None:
        """
        Get trivia question by trivia ID and order/position.

        Args:
            trivia_id: The trivia ID
            order: The question order/position

        Returns:
            TriviaQuestion entity or None if not found
        """
        pass

    @abstractmethod
    async def count_by_trivia(self, trivia_id: UUID) -> int:
        """
        Count questions in a trivia.

        Args:
            trivia_id: The trivia ID

        Returns:
            Number of questions in the trivia
        """
        pass

