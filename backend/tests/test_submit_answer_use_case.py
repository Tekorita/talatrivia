"""Tests for SubmitAnswerUseCase."""
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.application.use_cases.submit_answer import SubmitAnswerUseCase
from app.domain.entities.answer import Answer
from app.domain.entities.option import Option
from app.domain.entities.participation import Participation, ParticipationStatus
from app.domain.entities.question import Question, QuestionDifficulty
from app.domain.entities.trivia import Trivia, TriviaStatus
from app.domain.entities.trivia_question import TriviaQuestion
from app.domain.errors import InvalidStateError, NotFoundError
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
        self.answers = {}  # (trivia_id, user_id) -> list of answers with earned_points

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
        """Recompute score from answers."""
        key = (trivia_id, user_id)
        answers = self.answers.get(key, [])
        return sum(answer.get('earned_points', 0) for answer in answers)
    
    async def recompute_scores_for_trivia(self, trivia_id: UUID) -> None:
        """Recompute scores for all participations in trivia."""
        for (tid, uid), participation in self.participations.items():
            if tid == trivia_id:
                participation.score = await self.recompute_score(tid, uid)


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

    def __init__(self, participation_repo=None):
        self.answers = {}  # (participation_id, trivia_question_id) -> Answer
        self._unique_violations = set()
        self.participation_repo = participation_repo  # Reference to participation repo for score tracking

    async def get_by_participation_and_trivia_question(
        self, participation_id: UUID, trivia_question_id: UUID
    ):
        key = (participation_id, trivia_question_id)
        return self.answers.get(key)

    async def create(self, answer: Answer):
        key = (answer.participation_id, answer.trivia_question_id)
        if key in self.answers or key in self._unique_violations:
            from app.domain.errors import ConflictError
            raise ConflictError("Answer already submitted for this question")
        self.answers[key] = answer
        self._unique_violations.add(key)
        
        # Track answer for score recomputation
        if self.participation_repo:
            # Find participation to get trivia_id and user_id
            for (tid, uid), participation in self.participation_repo.participations.items():
                if participation.id == answer.participation_id:
                    answer_key = (tid, uid)
                    if answer_key not in self.participation_repo.answers:
                        self.participation_repo.answers[answer_key] = []
                    self.participation_repo.answers[answer_key].append({
                        'earned_points': answer.earned_points
                    })
                    break
        
        return answer


@pytest.mark.asyncio
async def test_submit_answer_correct_within_time():
    """Test submitting correct answer within time limit."""
    # Setup
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()
    correct_option_id = uuid4()
    wrong_option_id = uuid4()
    participation_id = uuid4()
    trivia_question_id = uuid4()

    started_at = (datetime.now(UTC) - timedelta(seconds=5)).replace(tzinfo=None)
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
    wrong_option = Option(
        id=wrong_option_id,
        question_id=question_id,
        text="3",
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
    option_repo.options[question_id] = [correct_option, wrong_option]

    answer_repo = InMemoryAnswerRepository(participation_repo=participation_repo)

    use_case = SubmitAnswerUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute
    result = await use_case.execute(trivia_id, user_id, correct_option_id)

    # Assert
    assert result.is_correct is True
    assert result.earned_points == 1  # EASY = 1 point
    assert result.total_score == 1
    assert result.time_remaining_seconds > 0


@pytest.mark.asyncio
async def test_submit_answer_incorrect():
    """Test submitting incorrect answer."""
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()
    correct_option_id = uuid4()
    wrong_option_id = uuid4()
    participation_id = uuid4()
    trivia_question_id = uuid4()

    started_at = (datetime.now(UTC) - timedelta(seconds=5)).replace(tzinfo=None)
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
    wrong_option = Option(
        id=wrong_option_id,
        question_id=question_id,
        text="3",
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
    option_repo.options[question_id] = [correct_option, wrong_option]

    answer_repo = InMemoryAnswerRepository(participation_repo=participation_repo)

    use_case = SubmitAnswerUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute
    result = await use_case.execute(trivia_id, user_id, wrong_option_id)

    # Assert
    assert result.is_correct is False
    assert result.earned_points == 0
    assert result.total_score == 0


@pytest.mark.asyncio
async def test_submit_answer_out_of_time():
    """Test submitting answer after time limit."""
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()
    correct_option_id = uuid4()
    participation_id = uuid4()
    trivia_question_id = uuid4()

    # Started 35 seconds ago, but time limit is 30 seconds
    started_at = (datetime.now(UTC) - timedelta(seconds=35)).replace(tzinfo=None)
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

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = participation

    trivia_question_repo = InMemoryTriviaQuestionRepository()
    trivia_question_repo.trivia_questions[(trivia_id, 0)] = trivia_question

    question_repo = InMemoryQuestionRepository()
    question_repo.questions[question_id] = question

    option_repo = InMemoryOptionRepository()
    option_repo.options[question_id] = [correct_option]

    answer_repo = InMemoryAnswerRepository(participation_repo=participation_repo)

    use_case = SubmitAnswerUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute
    result = await use_case.execute(trivia_id, user_id, correct_option_id)

    # Assert - should be 0 points even if correct, because out of time
    assert result.is_correct is False
    assert result.earned_points == 0
    assert result.total_score == 0
    assert result.time_remaining_seconds == 0


@pytest.mark.asyncio
async def test_submit_answer_duplicate():
    """Test submitting duplicate answer returns existing answer (idempotent)."""
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()
    option_id = uuid4()
    participation_id = uuid4()
    trivia_question_id = uuid4()

    started_at = (datetime.now(UTC) - timedelta(seconds=5)).replace(tzinfo=None)
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

    option = Option(
        id=option_id,
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
    option_repo.options[question_id] = [option]

    answer_repo = InMemoryAnswerRepository(participation_repo=participation_repo)

    use_case = SubmitAnswerUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # First submission
    result1 = await use_case.execute(trivia_id, user_id, option_id)
    assert result1.is_correct is True
    assert result1.earned_points == 1

    # Second submission should return the same result (idempotent)
    result2 = await use_case.execute(trivia_id, user_id, option_id)
    assert result2.is_correct == result1.is_correct
    assert result2.earned_points == result1.earned_points
    assert result2.selected_option_id == result1.selected_option_id


@pytest.mark.asyncio
async def test_submit_answer_no_question_started_at():
    """Test submit answer when question_started_at is None."""
    trivia_id = uuid4()
    user_id = uuid4()
    option_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
        question_started_at=None,  # None
    )

    participation = Participation(
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.READY,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = participation

    trivia_question_repo = InMemoryTriviaQuestionRepository()
    question_repo = InMemoryQuestionRepository()
    option_repo = InMemoryOptionRepository()
    answer_repo = InMemoryAnswerRepository(participation_repo=participation_repo)

    use_case = SubmitAnswerUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute & Assert
    with pytest.raises(InvalidStateError, match="Question has not been started"):
        await use_case.execute(trivia_id, user_id, option_id)


@pytest.mark.asyncio
async def test_submit_answer_trivia_question_not_found():
    """Test submit answer when trivia question doesn't exist."""
    trivia_id = uuid4()
    user_id = uuid4()
    option_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
        question_started_at=datetime.now(UTC).replace(tzinfo=None),
    )

    participation = Participation(
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.READY,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = participation

    trivia_question_repo = InMemoryTriviaQuestionRepository()
    # No trivia question added

    question_repo = InMemoryQuestionRepository()
    option_repo = InMemoryOptionRepository()
    answer_repo = InMemoryAnswerRepository(participation_repo=participation_repo)

    use_case = SubmitAnswerUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute & Assert
    with pytest.raises(NotFoundError, match="Question at index .* not found"):
        await use_case.execute(trivia_id, user_id, option_id)


@pytest.mark.asyncio
async def test_submit_answer_question_not_found():
    """Test submit answer when question doesn't exist."""
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()
    option_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
        question_started_at=datetime.now(UTC).replace(tzinfo=None),
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

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = participation

    trivia_question_repo = InMemoryTriviaQuestionRepository()
    trivia_question_repo.trivia_questions[(trivia_id, 0)] = trivia_question

    question_repo = InMemoryQuestionRepository()
    # No question added

    option_repo = InMemoryOptionRepository()
    answer_repo = InMemoryAnswerRepository(participation_repo=participation_repo)

    use_case = SubmitAnswerUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute & Assert
    with pytest.raises(NotFoundError, match="Question .* not found"):
        await use_case.execute(trivia_id, user_id, option_id)


@pytest.mark.asyncio
async def test_submit_answer_option_not_belongs_to_question():
    """Test submit answer when option doesn't belong to question."""
    trivia_id = uuid4()
    user_id = uuid4()
    question_id = uuid4()
    option_id = uuid4()
    wrong_option_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
        question_started_at=datetime.now(UTC).replace(tzinfo=None),
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

    option = Option(
        id=option_id,
        question_id=question_id,
        text="Correct",
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
    option_repo.options[question_id] = [option]  # Only option_id, not wrong_option_id

    answer_repo = InMemoryAnswerRepository(participation_repo=participation_repo)

    use_case = SubmitAnswerUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )

    # Execute & Assert - try to submit wrong_option_id
    with pytest.raises(NotFoundError, match="Option .* does not belong to question"):
        await use_case.execute(trivia_id, user_id, wrong_option_id)

