"""Tests for GetCurrentQuestionUseCase."""
import pytest
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
from app.application.use_cases.get_current_question import GetCurrentQuestionUseCase
from app.domain.entities.trivia import Trivia, TriviaStatus
from app.domain.entities.participation import Participation, ParticipationStatus
from app.domain.entities.trivia_question import TriviaQuestion
from app.domain.entities.question import Question, QuestionDifficulty
from app.domain.entities.option import Option
from app.domain.ports.trivia_repository import TriviaRepositoryPort
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.trivia_question_repository import TriviaQuestionRepositoryPort
from app.domain.ports.question_repository import QuestionRepositoryPort
from app.domain.ports.option_repository import OptionRepositoryPort
from app.domain.errors import NotFoundError, InvalidStateError


class InMemoryTriviaRepository(TriviaRepositoryPort):
    """In-memory trivia repository for testing."""

    def __init__(self):
        self.trivias = {}

    async def get_by_id(self, trivia_id: UUID):
        return self.trivias.get(trivia_id)

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
        self.participations[key] = participation

    async def list_by_trivia(self, trivia_id: UUID):
        return [
            p for (tid, _), p in self.participations.items()
            if tid == trivia_id
        ]


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


class InMemoryOptionRepository(OptionRepositoryPort):
    """In-memory option repository for testing."""

    def __init__(self):
        self.options = {}  # question_id -> list[Option]

    async def list_by_question_id(self, question_id: UUID):
        return self.options.get(question_id, [])


@pytest.mark.asyncio
async def test_get_current_question_success():
    """Test successful get current question."""
    # Setup
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()
    option1_id = uuid4()
    option2_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
        question_started_at=datetime.now(UTC),
        started_at=datetime.now(UTC),
    )

    participation = Participation(
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.READY,
    )

    trivia_question = TriviaQuestion(
        id=uuid4(),
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

    option1 = Option(
        id=option1_id,
        question_id=question_id,
        text="3",
        is_correct=False,
    )
    option2 = Option(
        id=option2_id,
        question_id=question_id,
        text="4",
        is_correct=True,
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
    option_repo.options[question_id] = [option1, option2]

    use_case = GetCurrentQuestionUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
    )

    # Execute
    result = await use_case.execute(trivia_id, user_id)

    # Assert
    assert result.question_id == question_id
    assert result.question_text == "What is 2+2?"
    assert len(result.options) == 2
    assert result.time_remaining_seconds >= 0
    assert result.time_remaining_seconds <= 30
    # Verify is_correct is not exposed
    assert not hasattr(result.options[0], "is_correct")


@pytest.mark.asyncio
async def test_get_current_question_trivia_not_in_progress():
    """Test get current question when trivia is not in progress."""
    trivia_id = uuid4()
    user_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.LOBBY,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    trivia_question_repo = InMemoryTriviaQuestionRepository()
    question_repo = InMemoryQuestionRepository()
    option_repo = InMemoryOptionRepository()

    use_case = GetCurrentQuestionUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
    )

    # Execute & Assert
    with pytest.raises(InvalidStateError):
        await use_case.execute(trivia_id, user_id)


@pytest.mark.asyncio
async def test_get_current_question_user_not_participating():
    """Test get current question when user is not participating."""
    trivia_id = uuid4()
    user_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    trivia_question_repo = InMemoryTriviaQuestionRepository()
    question_repo = InMemoryQuestionRepository()
    option_repo = InMemoryOptionRepository()

    use_case = GetCurrentQuestionUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
    )

    # Execute & Assert
    with pytest.raises(NotFoundError):
        await use_case.execute(trivia_id, user_id)


@pytest.mark.asyncio
async def test_get_current_question_time_remaining_calculation():
    """Test time remaining calculation."""
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()

    # Set question_started_at to 10 seconds ago
    started_at = datetime.now(UTC) - timedelta(seconds=10)
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
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.READY,
    )

    trivia_question = TriviaQuestion(
        id=uuid4(),
        trivia_id=trivia_id,
        question_id=question_id,
        position=0,
        time_limit_seconds=30,
    )

    question = Question(
        id=question_id,
        text="Test Question",
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
    option_repo.options[question_id] = []

    use_case = GetCurrentQuestionUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
    )

    # Execute
    result = await use_case.execute(trivia_id, user_id)

    # Assert - should be approximately 20 seconds remaining (30 - 10)
    assert result.time_remaining_seconds <= 20
    assert result.time_remaining_seconds >= 19  # Allow for small time differences

