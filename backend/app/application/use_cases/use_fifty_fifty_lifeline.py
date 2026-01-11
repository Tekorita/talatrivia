"""Use fifty-fifty lifeline use case."""
import random
from uuid import UUID

from app.application.dtos.fifty_fifty_dto import OptionDTO, UseFiftyFiftyResultDTO
from app.domain.enums.trivia_status import TriviaStatus
from app.domain.errors import ConflictError, InvalidStateError, NotFoundError
from app.domain.ports.answer_repository import AnswerRepositoryPort
from app.domain.ports.option_repository import OptionRepositoryPort
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.question_repository import QuestionRepositoryPort
from app.domain.ports.trivia_question_repository import TriviaQuestionRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort


class UseFiftyFiftyLifelineUseCase:
    """Use case for using the 50/50 lifeline."""

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
        question_id: UUID,
        user_id: UUID,
    ) -> UseFiftyFiftyResultDTO:
        """
        Execute use fifty-fifty lifeline use case.

        Args:
            trivia_id: The trivia ID
            question_id: The question ID to use the lifeline on
            user_id: The user ID

        Returns:
            UseFiftyFiftyResultDTO with 2 allowed options (1 correct + 1 incorrect)

        Raises:
            NotFoundError: If trivia, participation, question, or trivia_question doesn't exist
            ForbiddenError: If user is not assigned to trivia
            InvalidStateError: If trivia is not in IN_PROGRESS or question already answered
            ConflictError: If lifeline already used
        """
        # Get trivia
        trivia = await self.trivia_repository.get_by_id(trivia_id)
        if not trivia:
            raise NotFoundError(f"Trivia {trivia_id} not found")

        # Check trivia is in IN_PROGRESS
        if trivia.status != TriviaStatus.IN_PROGRESS:
            raise InvalidStateError(
                f"Cannot use lifeline when trivia is in status {trivia.status.value}"
            )

        # Get participation
        participation = await self.participation_repository.get_by_trivia_and_user(
            trivia_id, user_id
        )
        if not participation:
            raise NotFoundError(
                f"Participation not found for trivia {trivia_id} and user {user_id}"
            )

        # Check if lifeline already used
        if participation.fifty_fifty_used:
            raise ConflictError("50/50 lifeline has already been used for this trivia")

        # Verify question exists
        question = await self.question_repository.get_by_id(question_id)
        if not question:
            raise NotFoundError(f"Question {question_id} not found")

        # Get current trivia question
        trivia_question = await self.trivia_question_repository.get_by_trivia_and_order(
            trivia_id, trivia.current_question_index
        )
        if not trivia_question:
            raise NotFoundError(
                f"Question at index {trivia.current_question_index} not found for trivia {trivia_id}"
            )

        # Verify the question_id matches the current question
        if trivia_question.question_id != question_id:
            raise InvalidStateError(
                f"Question {question_id} is not the current question. "
                f"Current question ID is {trivia_question.question_id}"
            )

        # Check if question already answered
        existing_answer = await self.answer_repository.get_by_participation_and_trivia_question(
            participation.id, trivia_question.id
        )
        if existing_answer:
            raise InvalidStateError("Cannot use lifeline on an already answered question")

        # Get all options for the question
        options = await self.option_repository.list_by_question_id(question_id)

        if len(options) < 4:
            raise InvalidStateError(
                "Question must have at least 4 options to use 50/50 lifeline"
            )

        # Find correct option
        correct_option = next((opt for opt in options if opt.is_correct), None)
        if not correct_option:
            raise InvalidStateError("Question must have exactly one correct option")

        # Get incorrect options (excluding the correct one)
        incorrect_options = [opt for opt in options if not opt.is_correct]

        if len(incorrect_options) < 1:
            raise InvalidStateError("Question must have at least one incorrect option")

        # Randomly select one incorrect option
        selected_incorrect = random.choice(incorrect_options)

        # Build allowed options (correct + one incorrect, in random order)
        allowed_options_list = [correct_option, selected_incorrect]
        random.shuffle(allowed_options_list)

        # Update participation to mark lifeline as used
        participation.fifty_fifty_used = True
        participation.fifty_fifty_question_id = question_id
        await self.participation_repository.update(participation)

        # Build DTOs (without exposing is_correct)
        allowed_option_dtos = [
            OptionDTO(id=opt.id, text=opt.text) for opt in allowed_options_list
        ]

        return UseFiftyFiftyResultDTO(
            allowed_options=allowed_option_dtos,
            fifty_fifty_used=True,
        )

