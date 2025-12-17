"""Option repository port."""
from abc import ABC, abstractmethod
from uuid import UUID
from app.domain.entities.option import Option


class OptionRepositoryPort(ABC):
    """Port for option repository operations."""

    @abstractmethod
    async def list_by_question_id(self, question_id: UUID) -> list[Option]:
        """
        List all options for a question.

        Args:
            question_id: The question ID

        Returns:
            List of option entities
        """
        pass

