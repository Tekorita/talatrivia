"""Tests for UseFiftyFiftyLifelineUseCase."""
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.application.use_cases.use_fifty_fifty_lifeline import UseFiftyFiftyLifelineUseCase
from app.domain.entities.option import Option
from app.domain.entities.participation import Participation, ParticipationStatus
from app.domain.entities.question import Question, QuestionDifficulty
from app.domain.entities.trivia import Trivia, TriviaStatus
from app.domain.entities.trivia_question import TriviaQuestion
from app.domain.errors import ConflictError, InvalidStateError, NotFoundError
from app.domain.ports.answer_repository import AnswerRepositoryPort
from app.domain.ports.option_repository import OptionRepositoryPort
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.question_repository import QuestionRepositoryPort
from app.domain.ports.trivia_question_repository import TriviaQuestionRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort


class InMemoryTriviaRepository(TriviaRepositoryPort):
    """In-memory trivia repository for testing."""

    def __init__(self):
        self.trivias = {}

    async def get_by_id(self, trivia_id: UUID):
        return self.trivias.get(trivia_id)

    async def list_all(self):
        return list(self.trivias.values())

    async def create(self, trivia: Trivia):
        self.trivias[trivia.id] = trivia
        return trivia

    async def update(self, trivia: Trivia):
        self.trivias[trivia.id] = trivia


class InMemoryParticipationRepository(ParticipationRepositoryPort):
    """In-memory participation repository for testing."""

    def __init__(self):
        self.participations = {}

    async def get_by_trivia_and_user(self, trivia_id: UUID, user_id: UUID):
        key = (trivia_id, user_id)
        return self.participations.get(key)

    async def create(self, participation: Participation):
        key = (participation.trivia_id, participation.user_id)
        self.participations[key] = participation
        return participation

    async def update(self, participation: Participation):
        key = (participation.trivia_id, participation.user_id)
        if key in self.participations:
            self.participations[key] = participation

    async def list_by_trivia(self, trivia_id: UUID):
        return [
            p for (tid, _), p in self.participations.items()
            if tid == trivia_id
        ]
    
    async def list_by_user(self, user_id: UUID):
        return [
            p for (_, uid), p in self.participations.items()
            if uid == user_id
        ]
    
    async def recompute_score(self, trivia_id: UUID, user_id: UUID) -> int:
        """Recompute score from answers (mock implementation)."""
        participation = await self.get_by_trivia_and_user(trivia_id, user_id)
        if participation:
            return participation.score
        return 0
    
    async def recompute_scores_for_trivia(self, trivia_id: UUID) -> None:
        """Recompute scores for all participations in trivia (mock implementation)."""
        pass


class InMemoryTriviaQuestionRepository(TriviaQuestionRepositoryPort):
    """In-memory trivia question repository for testing."""

    def __init__(self):
        self.trivia_questions = {}

    async def get_by_trivia_and_order(self, trivia_id: UUID, order: int):
        key = (trivia_id, order)
        return self.trivia_questions.get(key)

    async def count_by_trivia(self, trivia_id: UUID) -> int:
        return sum(
            1 for (tid, _) in self.trivia_questions.keys()
            if tid == trivia_id
        )


class InMemoryQuestionRepository(QuestionRepositoryPort):
    """In-memory question repository for testing."""

    def __init__(self):
        self.questions = {}

    async def get_by_id(self, question_id: UUID):
        return self.questions.get(question_id)

    async def list_all(self):
        return list(self.questions.values())

    async def create(self, question: Question):
        self.questions[question.id] = question
        return question


class InMemoryOptionRepository(OptionRepositoryPort):
    """In-memory option repository for testing."""

    def __init__(self):
        self.options = {}  # question_id -> list[Option]

    async def list_by_question_id(self, question_id: UUID):
        return self.options.get(question_id, [])


class InMemoryAnswerRepository(AnswerRepositoryPort):
    """In-memory answer repository for testing."""

    def __init__(self):
        self.answers = {}  # (participation_id, trivia_question_id) -> Answer

    async def get_by_participation_and_trivia_question(
        self, participation_id: UUID, trivia_question_id: UUID
    ):
        key = (participation_id, trivia_question_id)
        return self.answers.get(key)

    async def create(self, answer):
        key = (answer.participation_id, answer.trivia_question_id)
        self.answers[key] = answer
        return answer


@pytest.mark.asyncio
async def test_use_fifty_fifty_lifeline_success():
    """Test using 50/50 lifeline successfully."""
    # Setup
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()
    participation_id = uuid4()
    trivia_question_id = uuid4()
    
    correct_option_id = uuid4()
    wrong_option_1_id = uuid4()
    wrong_option_2_id = uuid4()
    wrong_option_3_id = uuid4()

    started_at = datetime.now(UTC).replace(tzinfo=None)
    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
        question_started_at=started_at,
        started_at=started_at,
    )

    participation = Participation(
        id=participation_id,
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.READY,
        score=0,
        fifty_fifty_used=False,
        fifty_fifty_question_id=None,
    )

    trivia_question = TriviaQuestion(
        id=trivia_question_id,
        trivia_id=trivia_id,
        question_id=question_id,
        position=0,
        time_limit_seconds=30,
    )

    question = Question(
        id=question_id,
        text="What is 2+2?",
        difficulty=QuestionDifficulty.EASY,
    )

    correct_option = Option(
        id=correct_option_id,
        question_id=question_id,
        text="4",
        is_correct=True,
    )
    wrong_option_1 = Option(
        id=wrong_option_1_id,
        question_id=question_id,
        text="3",
        is_correct=False,
    )
    wrong_option_2 = Option(
        id=wrong_option_2_id,
        question_id=question_id,
        text="5",
        is_correct=False,
    )
    wrong_option_3 = Option(
        id=wrong_option_3_id,
        question_id=question_id,
        text="6",
        is_correct=False,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = participation

    trivia_question_repo = InMemoryTriviaQuestionRepository()
    trivia_question_repo.trivia_questions[(trivia_id, 0)] = trivia_question

    question_repo = InMemoryQuestionRepository()
    question_repo.questions[question_id] = question

    option_repo = InMemoryOptionRepository()
    option_repo.options[question_id] = [
        correct_option,
        wrong_option_1,
        wrong_option_2,
        wrong_option_3,
    ]

    answer_repo = InMemoryAnswerRepository()

    use_case = UseFiftyFiftyLifelineUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute
    result = await use_case.execute(trivia_id, question_id, user_id)

    # Assert
    assert result.fifty_fifty_used is True
    assert len(result.allowed_options) == 2
    
    # Verify one of the options is correct
    allowed_ids = [opt.id for opt in result.allowed_options]
    assert correct_option_id in allowed_ids
    
    # Verify participation was updated
    updated_participation = await participation_repo.get_by_trivia_and_user(trivia_id, user_id)
    assert updated_participation.fifty_fifty_used is True
    assert updated_participation.fifty_fifty_question_id == question_id


@pytest.mark.asyncio
async def test_use_fifty_fifty_lifeline_already_used():
    """Test using 50/50 lifeline when already used raises ConflictError."""
    # Setup
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()
    participation_id = uuid4()
    trivia_question_id = uuid4()

    started_at = datetime.now(UTC).replace(tzinfo=None)
    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
        question_started_at=started_at,
        started_at=started_at,
    )

    participation = Participation(
        id=participation_id,
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.READY,
        score=0,
        fifty_fifty_used=True,  # Already used
        fifty_fifty_question_id=uuid4(),
    )

    trivia_question = TriviaQuestion(
        id=trivia_question_id,
        trivia_id=trivia_id,
        question_id=question_id,
        position=0,
        time_limit_seconds=30,
    )

    question = Question(
        id=question_id,
        text="What is 2+2?",
        difficulty=QuestionDifficulty.EASY,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = participation

    trivia_question_repo = InMemoryTriviaQuestionRepository()
    trivia_question_repo.trivia_questions[(trivia_id, 0)] = trivia_question

    question_repo = InMemoryQuestionRepository()
    question_repo.questions[question_id] = question

    option_repo = InMemoryOptionRepository()
    option_repo.options[question_id] = [
        Option(id=uuid4(), question_id=question_id, text="4", is_correct=True),
        Option(id=uuid4(), question_id=question_id, text="3", is_correct=False),
        Option(id=uuid4(), question_id=question_id, text="5", is_correct=False),
        Option(id=uuid4(), question_id=question_id, text="6", is_correct=False),
    ]

    answer_repo = InMemoryAnswerRepository()

    use_case = UseFiftyFiftyLifelineUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute & Assert
    with pytest.raises(ConflictError, match="50/50 lifeline has already been used"):
        await use_case.execute(trivia_id, question_id, user_id)


@pytest.mark.asyncio
async def test_use_fifty_fifty_lifeline_trivia_not_in_progress():
    """Test using 50/50 lifeline when trivia is not IN_PROGRESS raises InvalidStateError."""
    # Setup
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()
    participation_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.LOBBY,  # Not IN_PROGRESS
        current_question_index=0,
    )

    participation = Participation(
        id=participation_id,
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.READY,
        score=0,
        fifty_fifty_used=False,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = participation

    trivia_question_repo = InMemoryTriviaQuestionRepository()
    question_repo = InMemoryQuestionRepository()
    option_repo = InMemoryOptionRepository()
    answer_repo = InMemoryAnswerRepository()

    use_case = UseFiftyFiftyLifelineUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute & Assert
    with pytest.raises(InvalidStateError, match="Cannot use lifeline when trivia is in status"):
        await use_case.execute(trivia_id, question_id, user_id)


@pytest.mark.asyncio
async def test_use_fifty_fifty_lifeline_wrong_question():
    """Test using 50/50 lifeline on wrong question raises InvalidStateError."""
    # Setup
    trivia_id = uuid4()
    user_id = uuid4()
    wrong_question_id = uuid4()  # Different from current question
    current_question_id = uuid4()
    participation_id = uuid4()
    trivia_question_id = uuid4()

    started_at = datetime.now(UTC).replace(tzinfo=None)
    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
        question_started_at=started_at,
        started_at=started_at,
    )

    participation = Participation(
        id=participation_id,
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.READY,
        score=0,
        fifty_fifty_used=False,
    )

    trivia_question = TriviaQuestion(
        id=trivia_question_id,
        trivia_id=trivia_id,
        question_id=current_question_id,  # Current question is different
        position=0,
        time_limit_seconds=30,
    )

    # Create both questions so they exist in the repository
    current_question = Question(
        id=current_question_id,
        text="Current question",
        difficulty=QuestionDifficulty.EASY,
    )
    
    wrong_question = Question(
        id=wrong_question_id,
        text="Wrong question",
        difficulty=QuestionDifficulty.EASY,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = participation

    trivia_question_repo = InMemoryTriviaQuestionRepository()
    trivia_question_repo.trivia_questions[(trivia_id, 0)] = trivia_question

    question_repo = InMemoryQuestionRepository()
    question_repo.questions[current_question_id] = current_question
    question_repo.questions[wrong_question_id] = wrong_question  # Add wrong question to repo

    option_repo = InMemoryOptionRepository()
    answer_repo = InMemoryAnswerRepository()

    use_case = UseFiftyFiftyLifelineUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute & Assert
    with pytest.raises(InvalidStateError, match="is not the current question"):
        await use_case.execute(trivia_id, wrong_question_id, user_id)


@pytest.mark.asyncio
async def test_use_fifty_fifty_lifeline_question_already_answered():
    """Test using 50/50 lifeline on already answered question raises InvalidStateError."""
    # Setup
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()
    participation_id = uuid4()
    trivia_question_id = uuid4()

    started_at = datetime.now(UTC).replace(tzinfo=None)
    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
        question_started_at=started_at,
        started_at=started_at,
    )

    participation = Participation(
        id=participation_id,
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.READY,
        score=0,
        fifty_fifty_used=False,
    )

    trivia_question = TriviaQuestion(
        id=trivia_question_id,
        trivia_id=trivia_id,
        question_id=question_id,
        position=0,
        time_limit_seconds=30,
    )

    question = Question(
        id=question_id,
        text="What is 2+2?",
        difficulty=QuestionDifficulty.EASY,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = participation

    trivia_question_repo = InMemoryTriviaQuestionRepository()
    trivia_question_repo.trivia_questions[(trivia_id, 0)] = trivia_question

    question_repo = InMemoryQuestionRepository()
    question_repo.questions[question_id] = question

    option_repo = InMemoryOptionRepository()
    option_repo.options[question_id] = [
        Option(id=uuid4(), question_id=question_id, text="4", is_correct=True),
        Option(id=uuid4(), question_id=question_id, text="3", is_correct=False),
        Option(id=uuid4(), question_id=question_id, text="5", is_correct=False),
        Option(id=uuid4(), question_id=question_id, text="6", is_correct=False),
    ]

    answer_repo = InMemoryAnswerRepository()
    # Create an answer to simulate already answered
    from app.domain.entities.answer import Answer
    answer = Answer(
        id=uuid4(),
        participation_id=participation_id,
        trivia_question_id=trivia_question_id,
        selected_option_id=uuid4(),
        is_correct=True,
        earned_points=1,
        answered_at=datetime.now(UTC),
    )
    answer_repo.answers[(participation_id, trivia_question_id)] = answer

    use_case = UseFiftyFiftyLifelineUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute & Assert
    with pytest.raises(InvalidStateError, match="Cannot use lifeline on an already answered question"):
        await use_case.execute(trivia_id, question_id, user_id)


@pytest.mark.asyncio
async def test_use_fifty_fifty_lifeline_returns_correct_and_incorrect():
    """Test that 50/50 lifeline returns exactly 1 correct and 1 incorrect option."""
    # Setup
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()
    participation_id = uuid4()
    trivia_question_id = uuid4()
    
    correct_option_id = uuid4()
    wrong_option_1_id = uuid4()
    wrong_option_2_id = uuid4()
    wrong_option_3_id = uuid4()

    started_at = datetime.now(UTC).replace(tzinfo=None)
    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
        question_started_at=started_at,
        started_at=started_at,
    )

    participation = Participation(
        id=participation_id,
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.READY,
        score=0,
        fifty_fifty_used=False,
    )

    trivia_question = TriviaQuestion(
        id=trivia_question_id,
        trivia_id=trivia_id,
        question_id=question_id,
        position=0,
        time_limit_seconds=30,
    )

    question = Question(
        id=question_id,
        text="What is 2+2?",
        difficulty=QuestionDifficulty.EASY,
    )

    correct_option = Option(
        id=correct_option_id,
        question_id=question_id,
        text="4",
        is_correct=True,
    )
    wrong_option_1 = Option(
        id=wrong_option_1_id,
        question_id=question_id,
        text="3",
        is_correct=False,
    )
    wrong_option_2 = Option(
        id=wrong_option_2_id,
        question_id=question_id,
        text="5",
        is_correct=False,
    )
    wrong_option_3 = Option(
        id=wrong_option_3_id,
        question_id=question_id,
        text="6",
        is_correct=False,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = participation

    trivia_question_repo = InMemoryTriviaQuestionRepository()
    trivia_question_repo.trivia_questions[(trivia_id, 0)] = trivia_question

    question_repo = InMemoryQuestionRepository()
    question_repo.questions[question_id] = question

    option_repo = InMemoryOptionRepository()
    option_repo.options[question_id] = [
        correct_option,
        wrong_option_1,
        wrong_option_2,
        wrong_option_3,
    ]

    answer_repo = InMemoryAnswerRepository()

    use_case = UseFiftyFiftyLifelineUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute
    result = await use_case.execute(trivia_id, question_id, user_id)

    # Assert
    assert len(result.allowed_options) == 2
    
    # Verify correct option is included
    allowed_ids = [opt.id for opt in result.allowed_options]
    assert correct_option_id in allowed_ids
    
    # Verify exactly one incorrect option is included
    all_wrong_ids = [wrong_option_1_id, wrong_option_2_id, wrong_option_3_id]
    wrong_in_allowed = [opt_id for opt_id in allowed_ids if opt_id in all_wrong_ids]
    assert len(wrong_in_allowed) == 1


@pytest.mark.asyncio
async def test_use_fifty_fifty_lifeline_trivia_not_found():
    """Test using 50/50 lifeline when trivia doesn't exist raises NotFoundError."""
    # Setup
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()

    trivia_repo = InMemoryTriviaRepository()
    participation_repo = InMemoryParticipationRepository()
    trivia_question_repo = InMemoryTriviaQuestionRepository()
    question_repo = InMemoryQuestionRepository()
    option_repo = InMemoryOptionRepository()
    answer_repo = InMemoryAnswerRepository()

    use_case = UseFiftyFiftyLifelineUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute & Assert
    with pytest.raises(NotFoundError, match="Trivia .* not found"):
        await use_case.execute(trivia_id, question_id, user_id)


@pytest.mark.asyncio
async def test_use_fifty_fifty_lifeline_participation_not_found():
    """Test using 50/50 lifeline when participation doesn't exist raises NotFoundError."""
    # Setup
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()

    started_at = datetime.now(UTC).replace(tzinfo=None)
    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
        question_started_at=started_at,
        started_at=started_at,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    trivia_question_repo = InMemoryTriviaQuestionRepository()
    question_repo = InMemoryQuestionRepository()
    option_repo = InMemoryOptionRepository()
    answer_repo = InMemoryAnswerRepository()

    use_case = UseFiftyFiftyLifelineUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute & Assert
    with pytest.raises(NotFoundError, match="Participation not found"):
        await use_case.execute(trivia_id, question_id, user_id)

