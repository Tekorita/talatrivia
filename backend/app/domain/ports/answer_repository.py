"""Answer repository port."""
from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.answer import Answer


class AnswerRepositoryPort(ABC):
    """Port for answer repository operations."""

    @abstractmethod
    async def get_by_participation_and_trivia_question(
        self, participation_id: UUID, trivia_question_id: UUID
    ) -> Answer | None:
        """
        Get answer by participation and trivia question.

        Args:
            participation_id: The participation ID
            trivia_question_id: The trivia question ID

        Returns:
            Answer entity or None if not found
        """
        pass

    @abstractmethod
    async def create(self, answer: Answer) -> Answer:
        """
        Create a new answer.

        Args:
            answer: The answer entity to create

        Returns:
            The created answer
        """
        pass

