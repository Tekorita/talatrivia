"""Get current question use case."""
from datetime import UTC, datetime
from uuid import UUID

from app.application.dtos.current_question_dto import CurrentQuestionDTO, OptionDTO
from app.domain.enums.trivia_status import TriviaStatus
from app.domain.errors import InvalidStateError, NotFoundError
from app.domain.ports.option_repository import OptionRepositoryPort
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.question_repository import QuestionRepositoryPort
from app.domain.ports.trivia_question_repository import TriviaQuestionRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort


class GetCurrentQuestionUseCase:
    """Use case for getting the current question of a trivia."""

    def __init__(
        self,
        trivia_repository: TriviaRepositoryPort,
        participation_repository: ParticipationRepositoryPort,
        trivia_question_repository: TriviaQuestionRepositoryPort,
        question_repository: QuestionRepositoryPort,
        option_repository: OptionRepositoryPort,
    ):
        self.trivia_repository = trivia_repository
        self.participation_repository = participation_repository
        self.trivia_question_repository = trivia_question_repository
        self.question_repository = question_repository
        self.option_repository = option_repository

    async def execute(
        self, trivia_id: UUID, user_id: UUID
    ) -> CurrentQuestionDTO:
        """
        Execute get current question use case.

        Args:
            trivia_id: The trivia ID
            user_id: The user ID (for participation validation)

        Returns:
            CurrentQuestionDTO with question and options (without correct answer)

        Raises:
            NotFoundError: If trivia, participation, or question doesn't exist
            InvalidStateError: If trivia is not in IN_PROGRESS
        """
        # Get trivia
        trivia = await self.trivia_repository.get_by_id(trivia_id)
        if not trivia:
            raise NotFoundError(f"Trivia {trivia_id} not found")

        # Check trivia is in IN_PROGRESS
        if trivia.status != TriviaStatus.IN_PROGRESS:
            raise InvalidStateError(
                f"Trivia is not in progress. Current status: {trivia.status.value}"
            )

        # Check participation exists
        participation = await self.participation_repository.get_by_trivia_and_user(
            trivia_id, user_id
        )
        if not participation:
            raise NotFoundError(
                f"Participation not found for trivia {trivia_id} and user {user_id}"
            )

        # Get trivia question using current_question_index
        trivia_question = await self.trivia_question_repository.get_by_trivia_and_order(
            trivia_id, trivia.current_question_index
        )
        if not trivia_question:
            raise NotFoundError(
                f"Question at index {trivia.current_question_index} not found for trivia {trivia_id}"
            )

        # Get question
        question = await self.question_repository.get_by_id(trivia_question.question_id)
        if not question:
            raise NotFoundError(
                f"Question {trivia_question.question_id} not found"
            )

        # Get options
        options = await self.option_repository.list_by_question_id(question.id)

        # Calculate time remaining
        # Note: trivia.question_started_at is naive UTC (from DB), so we need to make now naive UTC too
        if trivia.question_started_at:
            # Convert current UTC time to naive UTC (same as stored in DB)
            # Use the same conversion method as _to_naive_dt in trivia_mapper
            now_aware = datetime.now(UTC)
            now_naive = now_aware.astimezone(UTC).replace(tzinfo=None)
            
            # Calculate elapsed time
            elapsed = (now_naive - trivia.question_started_at).total_seconds()
            
            # Safety check: if elapsed is negative, it means question_started_at is in the future
            # This shouldn't happen but if it does, treat as 0 elapsed (question just started)
            if elapsed < 0:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"❌ Negative elapsed time detected! question_started_at: {trivia.question_started_at}, "
                    f"now_naive: {now_naive}, elapsed: {elapsed:.2f}s. "
                    f"This suggests a timezone conversion issue. Treating as 0 elapsed."
                )
                elapsed = 0
            
            # Calculate remaining time
            remaining = trivia_question.time_limit_seconds - int(elapsed)
            time_remaining_seconds = max(0, remaining)
        else:
            # If question_started_at is None, return full time limit
            time_remaining_seconds = trivia_question.time_limit_seconds

        # Build DTO without exposing is_correct or difficulty
        option_dtos = [
            OptionDTO(option_id=option.id, option_text=option.text)
            for option in options
        ]

        # Check if fifty-fifty lifeline is available
        fifty_fifty_available = not participation.fifty_fifty_used

        return CurrentQuestionDTO(
            question_id=question.id,
            question_text=question.text,
            options=option_dtos,
            time_remaining_seconds=time_remaining_seconds,
            fifty_fifty_available=fifty_fifty_available,
        )

