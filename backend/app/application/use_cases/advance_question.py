"""Advance question use case."""
from datetime import UTC, datetime
from uuid import UUID

from app.application.dtos.advance_question_dto import AdvanceQuestionResultDTO
from app.domain.enums.trivia_status import TriviaStatus
from app.domain.errors import ForbiddenError, InvalidStateError, NotFoundError
from app.domain.ports.trivia_question_repository import TriviaQuestionRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort


class AdvanceQuestionUseCase:
    """Use case for advancing to the next question or finishing the trivia."""

    def __init__(
        self,
        trivia_repository: TriviaRepositoryPort,
        trivia_question_repository: TriviaQuestionRepositoryPort,
    ):
        self.trivia_repository = trivia_repository
        self.trivia_question_repository = trivia_question_repository

    async def execute(
        self,
        trivia_id: UUID,
        admin_user_id: UUID,
    ) -> AdvanceQuestionResultDTO:
        """
        Execute advance question use case.

        Args:
            trivia_id: The trivia ID
            admin_user_id: The admin user ID (must be creator)

        Returns:
            AdvanceQuestionResultDTO with updated trivia state

        Raises:
            NotFoundError: If trivia doesn't exist
            ForbiddenError: If user is not the creator
            InvalidStateError: If trivia is not in IN_PROGRESS
        """
        # Get trivia
        trivia = await self.trivia_repository.get_by_id(trivia_id)
        if not trivia:
            raise NotFoundError(f"Trivia {trivia_id} not found")

        # Check user is creator
        if trivia.created_by_user_id != admin_user_id:
            raise ForbiddenError(
                f"User {admin_user_id} is not authorized to advance question for trivia {trivia_id}"
            )

        # Check trivia is in IN_PROGRESS
        if trivia.status != TriviaStatus.IN_PROGRESS:
            raise InvalidStateError(
                f"Cannot advance question when trivia is in status {trivia.status.value}"
            )

        # Get total questions
        total_questions = await self.trivia_question_repository.count_by_trivia(trivia_id)

        # Check if there are more questions
        if trivia.current_question_index + 1 < total_questions:
            # Advance to next question
            trivia.current_question_index += 1
            trivia.question_started_at = datetime.now(UTC)
            # Keep status IN_PROGRESS
        else:
            # No more questions, finish trivia
            trivia.status = TriviaStatus.FINISHED
            trivia.question_started_at = None
            trivia.finished_at = datetime.now(UTC)

        # Update trivia
        await self.trivia_repository.update(trivia)

        return AdvanceQuestionResultDTO(
            trivia_id=trivia_id,
            status=trivia.status,
            current_question_index=trivia.current_question_index,
            total_questions=total_questions,
        )

