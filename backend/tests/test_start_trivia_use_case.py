"""Tests for StartTriviaUseCase."""
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.application.use_cases.start_trivia import StartTriviaUseCase
from app.domain.entities.participation import Participation, ParticipationStatus
from app.domain.entities.trivia import Trivia, TriviaStatus
from app.domain.errors import ForbiddenError, InvalidStateError, NotFoundError
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort


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
            p for (tid, _), p in self.participations.items() if tid == trivia_id
        ]


@pytest.mark.asyncio
async def test_start_trivia_success():
    """Test successful trivia start."""
    # Setup
    trivia_id = uuid4()
    admin_user_id = uuid4()
    user_id_1 = uuid4()
    user_id_2 = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=admin_user_id,
        status=TriviaStatus.LOBBY,
    )

    participation_1 = Participation(
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id_1,
        status=ParticipationStatus.READY,
    )
    participation_2 = Participation(
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id_2,
        status=ParticipationStatus.JOINED,  # Not ready
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id_1)] = participation_1
    participation_repo.participations[(trivia_id, user_id_2)] = participation_2

    use_case = StartTriviaUseCase(trivia_repo, participation_repo)

    # Execute
    result = await use_case.execute(trivia_id, admin_user_id)

    # Assert
    assert result.trivia_id == trivia_id
    assert result.trivia_status == TriviaStatus.IN_PROGRESS
    assert result.current_question_index == 0
    assert result.started_at is not None

    # Verify trivia was updated
    updated_trivia = trivia_repo.trivias[trivia_id]
    assert updated_trivia.status == TriviaStatus.IN_PROGRESS
    assert updated_trivia.started_at is not None
    assert updated_trivia.current_question_index == 0
    assert updated_trivia.question_started_at is not None


@pytest.mark.asyncio
async def test_start_trivia_not_found():
    """Test start trivia when trivia doesn't exist."""
    trivia_id = uuid4()
    admin_user_id = uuid4()

    trivia_repo = InMemoryTriviaRepository()
    participation_repo = InMemoryParticipationRepository()

    use_case = StartTriviaUseCase(trivia_repo, participation_repo)

    # Execute & Assert
    with pytest.raises(NotFoundError, match="Trivia .* not found"):
        await use_case.execute(trivia_id, admin_user_id)


@pytest.mark.asyncio
async def test_start_trivia_forbidden():
    """Test start trivia when user is not the creator."""
    trivia_id = uuid4()
    admin_user_id = uuid4()
    other_user_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=admin_user_id,
        status=TriviaStatus.LOBBY,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()

    use_case = StartTriviaUseCase(trivia_repo, participation_repo)

    # Execute & Assert
    with pytest.raises(ForbiddenError, match="not authorized"):
        await use_case.execute(trivia_id, other_user_id)


@pytest.mark.asyncio
async def test_start_trivia_invalid_state():
    """Test start trivia when trivia is not in LOBBY."""
    trivia_id = uuid4()
    admin_user_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=admin_user_id,
        status=TriviaStatus.IN_PROGRESS,  # Not LOBBY
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()

    use_case = StartTriviaUseCase(trivia_repo, participation_repo)

    # Execute & Assert
    with pytest.raises(InvalidStateError, match="Cannot start trivia in status"):
        await use_case.execute(trivia_id, admin_user_id)


@pytest.mark.asyncio
async def test_start_trivia_no_ready_players():
    """Test start trivia when no players are READY."""
    trivia_id = uuid4()
    admin_user_id = uuid4()
    user_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=admin_user_id,
        status=TriviaStatus.LOBBY,
    )

    participation = Participation(
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.JOINED,  # Not READY
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = participation

    use_case = StartTriviaUseCase(trivia_repo, participation_repo)

    # Execute & Assert
    with pytest.raises(InvalidStateError, match="at least one player must be READY"):
        await use_case.execute(trivia_id, admin_user_id)

