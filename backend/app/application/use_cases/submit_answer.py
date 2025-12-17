"""Submit answer use case."""
import uuid
from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import UUID
from app.application.dtos.submit_answer_dto import SubmitAnswerResultDTO
from app.domain.entities.answer import Answer
from app.domain.enums.trivia_status import TriviaStatus
from app.domain.errors import ConflictError, InvalidStateError, NotFoundError
from app.domain.ports.answer_repository import AnswerRepositoryPort
from app.domain.ports.option_repository import OptionRepositoryPort
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.question_repository import QuestionRepositoryPort
from app.domain.ports.trivia_question_repository import TriviaQuestionRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort
from app.domain.enums.difficulty import Difficulty
from app.domain.services.score_service import ScoreService


class SubmitAnswerUseCase:
    """Use case for submitting an answer to a trivia question."""

    def __init__(
        self,
        trivia_repository: TriviaRepositoryPort,
        participation_repository: ParticipationRepositoryPort,
        trivia_question_repository: TriviaQuestionRepositoryPort,
        question_repository: QuestionRepositoryPort,
        option_repository: OptionRepositoryPort,
        answer_repository: AnswerRepositoryPort,
    ):
        self.trivia_repository = trivia_repository
        self.participation_repository = participation_repository
        self.trivia_question_repository = trivia_question_repository
        self.question_repository = question_repository
        self.option_repository = option_repository
        self.answer_repository = answer_repository

    async def execute(
        self,
        trivia_id: UUID,
        user_id: UUID,
        selected_option_id: UUID,
        answered_at: Optional[datetime] = None,
    ) -> SubmitAnswerResultDTO:
        """
        Execute submit answer use case.

        Args:
            trivia_id: The trivia ID
            user_id: The user ID
            selected_option_id: The selected option ID
            answered_at: Optional timestamp (defaults to now)

        Returns:
            SubmitAnswerResultDTO with answer result and score

        Raises:
            NotFoundError: If trivia, participation, question, or option doesn't exist
            InvalidStateError: If trivia is not in progress or time expired
            ConflictError: If answer already submitted
        """
        if answered_at is None:
            answered_at = datetime.now(UTC)

        # Get trivia
        trivia = await self.trivia_repository.get_by_id(trivia_id)
        if not trivia:
            raise NotFoundError(f"Trivia {trivia_id} not found")

        # Check trivia is in IN_PROGRESS
        if trivia.status != TriviaStatus.IN_PROGRESS:
            raise InvalidStateError(
                f"Trivia is not in progress. Current status: {trivia.status.value}"
            )

        # Check question_started_at exists
        if not trivia.question_started_at:
            raise InvalidStateError("Question has not been started")

        # Get participation
        participation = await self.participation_repository.get_by_trivia_and_user(
            trivia_id, user_id
        )
        if not participation:
            raise NotFoundError(
                f"Participation not found for trivia {trivia_id} and user {user_id}"
            )

        # Get current trivia question
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

        # Get all options for the question
        options = await self.option_repository.list_by_question_id(question.id)

        # Validate selected option belongs to current question
        selected_option = next(
            (opt for opt in options if opt.id == selected_option_id), None
        )
        if not selected_option:
            raise NotFoundError(
                f"Option {selected_option_id} does not belong to question {question.id}"
            )

        # Soft check: verify answer doesn't already exist
        existing_answer = await self.answer_repository.get_by_participation_and_trivia_question(
            participation.id, trivia_question.id
        )
        if existing_answer:
            raise ConflictError("Answer already submitted for this question")

        # Calculate time remaining
        elapsed = (answered_at - trivia.question_started_at).total_seconds()
        remaining = trivia_question.time_limit_seconds - int(elapsed)
        time_remaining_seconds = max(0, remaining)

        # Determine if answer is correct and calculate points
        is_correct = selected_option.is_correct
        if time_remaining_seconds <= 0:
            # Out of time
            earned_points = 0
            is_correct = False
        elif is_correct:
            # Correct answer within time
            # Map QuestionDifficulty value to Difficulty enum
            difficulty = Difficulty(question.difficulty.value)
            earned_points = ScoreService.points_for(difficulty)
        else:
            # Incorrect answer
            earned_points = 0

        # Create answer entity
        answer = Answer(
            id=uuid.uuid4(),
            participation_id=participation.id,
            trivia_question_id=trivia_question.id,
            selected_option_id=selected_option_id,
            is_correct=is_correct,
            earned_points=earned_points,
            answered_at=answered_at,
        )

        # Persist answer and update participation score in transaction
        # Note: Both operations use the same session, so they're in the same transaction
        try:
            created_answer = await self.answer_repository.create(answer)
            # Update participation score
            participation.score += earned_points
            await self.participation_repository.update(participation)
        except ConflictError:
            # Re-raise ConflictError from repository
            raise
        except Exception as e:
            # Check if it's a unique constraint violation (fallback)
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                raise ConflictError("Answer already submitted for this question") from e
            raise

        return SubmitAnswerResultDTO(
            trivia_id=trivia_id,
            question_id=question.id,
            selected_option_id=selected_option_id,
            is_correct=is_correct,
            earned_points=earned_points,
            total_score=participation.score,
            time_remaining_seconds=time_remaining_seconds,
        )

