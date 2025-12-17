"""Tests for AdvanceQuestionUseCase."""
from datetime import UTC, datetime, timedelta
from typing import Dict
from uuid import UUID, uuid4

import pytest

from app.application.use_cases.advance_question import AdvanceQuestionUseCase
from app.domain.entities.trivia import Trivia, TriviaStatus
from app.domain.entities.trivia_question import TriviaQuestion
from app.domain.errors import ForbiddenError, InvalidStateError, NotFoundError
from app.domain.ports.trivia_question_repository import TriviaQuestionRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort


class InMemoryTriviaRepository(TriviaRepositoryPort):
    """In-memory trivia repository for testing."""

    def __init__(self):
        self.trivias: Dict[UUID, Trivia] = {}

    async def get_by_id(self, trivia_id: UUID) -> Trivia | None:
        return self.trivias.get(trivia_id)

    async def update(self, trivia: Trivia) -> None:
        self.trivias[trivia.id] = trivia


class InMemoryTriviaQuestionRepository(TriviaQuestionRepositoryPort):
    """In-memory trivia question repository for testing."""

    def __init__(self):
        self.trivia_questions: Dict[UUID, TriviaQuestion] = {}

    async def get_by_trivia_and_order(
        self, trivia_id: UUID, order: int
    ) -> TriviaQuestion | None:
        return next(
            (
                tq
                for tq in self.trivia_questions.values()
                if tq.trivia_id == trivia_id and tq.position == order
            ),
            None,
        )

    async def count_by_trivia(self, trivia_id: UUID) -> int:
        return sum(
            1 for tq in self.trivia_questions.values() if tq.trivia_id == trivia_id
        )


@pytest.mark.asyncio
async def test_advance_question_success():
    """Test successful advance to next question."""
    # Setup
    trivia_id = uuid4()
    admin_user_id = uuid4()
    question_id_1 = uuid4()
    question_id_2 = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=admin_user_id,
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
        question_started_at=datetime.now(UTC) - timedelta(seconds=10),
    )

    trivia_question_1 = TriviaQuestion(
        id=uuid4(),
        trivia_id=trivia_id,
        question_id=question_id_1,
        position=0,
        time_limit_seconds=30,
    )
    trivia_question_2 = TriviaQuestion(
        id=uuid4(),
        trivia_id=trivia_id,
        question_id=question_id_2,
        position=1,
        time_limit_seconds=30,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    trivia_question_repo = InMemoryTriviaQuestionRepository()
    trivia_question_repo.trivia_questions[trivia_question_1.id] = trivia_question_1
    trivia_question_repo.trivia_questions[trivia_question_2.id] = trivia_question_2

    use_case = AdvanceQuestionUseCase(trivia_repo, trivia_question_repo)

    # Execute
    result = await use_case.execute(trivia_id, admin_user_id)

    # Assert
    assert result.trivia_id == trivia_id
    assert result.status == TriviaStatus.IN_PROGRESS
    assert result.current_question_index == 1
    assert result.total_questions == 2

    # Verify trivia was updated
    updated_trivia = trivia_repo.trivias[trivia_id]
    assert updated_trivia.current_question_index == 1
    assert updated_trivia.status == TriviaStatus.IN_PROGRESS
    assert updated_trivia.question_started_at is not None


@pytest.mark.asyncio
async def test_advance_question_finish_trivia():
    """Test finishing trivia when no more questions."""
    # Setup
    trivia_id = uuid4()
    admin_user_id = uuid4()
    question_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=admin_user_id,
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
        question_started_at=datetime.now(UTC) - timedelta(seconds=10),
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

    trivia_question_repo = InMemoryTriviaQuestionRepository()
    trivia_question_repo.trivia_questions[trivia_question.id] = trivia_question

    use_case = AdvanceQuestionUseCase(trivia_repo, trivia_question_repo)

    # Execute
    result = await use_case.execute(trivia_id, admin_user_id)

    # Assert
    assert result.trivia_id == trivia_id
    assert result.status == TriviaStatus.FINISHED
    assert result.current_question_index == 0
    assert result.total_questions == 1

    # Verify trivia was updated
    updated_trivia = trivia_repo.trivias[trivia_id]
    assert updated_trivia.status == TriviaStatus.FINISHED
    assert updated_trivia.question_started_at is None
    assert updated_trivia.finished_at is not None


@pytest.mark.asyncio
async def test_advance_question_not_found():
    """Test advance question when trivia doesn't exist."""
    trivia_id = uuid4()
    admin_user_id = uuid4()

    trivia_repo = InMemoryTriviaRepository()
    trivia_question_repo = InMemoryTriviaQuestionRepository()

    use_case = AdvanceQuestionUseCase(trivia_repo, trivia_question_repo)

    # Execute & Assert
    with pytest.raises(NotFoundError, match="Trivia .* not found"):
        await use_case.execute(trivia_id, admin_user_id)


@pytest.mark.asyncio
async def test_advance_question_forbidden():
    """Test advance question when user is not the creator."""
    # Setup
    trivia_id = uuid4()
    admin_user_id = uuid4()
    other_user_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=admin_user_id,
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=0,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    trivia_question_repo = InMemoryTriviaQuestionRepository()

    use_case = AdvanceQuestionUseCase(trivia_repo, trivia_question_repo)

    # Execute & Assert
    with pytest.raises(ForbiddenError, match="not authorized"):
        await use_case.execute(trivia_id, other_user_id)


@pytest.mark.asyncio
async def test_advance_question_invalid_state():
    """Test advance question when trivia is not in progress."""
    # Setup
    trivia_id = uuid4()
    admin_user_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=admin_user_id,
        status=TriviaStatus.LOBBY,  # Not IN_PROGRESS
        current_question_index=0,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    trivia_question_repo = InMemoryTriviaQuestionRepository()

    use_case = AdvanceQuestionUseCase(trivia_repo, trivia_question_repo)

    # Execute & Assert
    with pytest.raises(InvalidStateError, match="Cannot advance question when trivia is in status"):
        await use_case.execute(trivia_id, admin_user_id)


@pytest.mark.asyncio
async def test_advance_question_last_question():
    """Test advance question when on last question (should finish)."""
    # Setup
    trivia_id = uuid4()
    admin_user_id = uuid4()
    question_id_1 = uuid4()
    question_id_2 = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=admin_user_id,
        status=TriviaStatus.IN_PROGRESS,
        current_question_index=1,  # On second question (index 1)
        question_started_at=datetime.now(UTC) - timedelta(seconds=10),
    )

    trivia_question_1 = TriviaQuestion(
        id=uuid4(),
        trivia_id=trivia_id,
        question_id=question_id_1,
        position=0,
        time_limit_seconds=30,
    )
    trivia_question_2 = TriviaQuestion(
        id=uuid4(),
        trivia_id=trivia_id,
        question_id=question_id_2,
        position=1,
        time_limit_seconds=30,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    trivia_question_repo = InMemoryTriviaQuestionRepository()
    trivia_question_repo.trivia_questions[trivia_question_1.id] = trivia_question_1
    trivia_question_repo.trivia_questions[trivia_question_2.id] = trivia_question_2

    use_case = AdvanceQuestionUseCase(trivia_repo, trivia_question_repo)

    # Execute
    result = await use_case.execute(trivia_id, admin_user_id)

    # Assert
    assert result.status == TriviaStatus.FINISHED
    assert result.current_question_index == 1  # Still on last question
    assert result.total_questions == 2

    # Verify trivia was finished
    updated_trivia = trivia_repo.trivias[trivia_id]
    assert updated_trivia.status == TriviaStatus.FINISHED
    assert updated_trivia.question_started_at is None
    assert updated_trivia.finished_at is not None

