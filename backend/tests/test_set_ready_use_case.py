"""Tests for SetReadyUseCase."""
from uuid import UUID, uuid4

import pytest

from app.application.use_cases.set_ready import SetReadyUseCase
from app.domain.entities.participation import Participation, ParticipationStatus
from app.domain.entities.trivia import Trivia, TriviaStatus
from app.domain.errors import InvalidStateError, NotFoundError
from app.domain.ports.participation_repository import ParticipationRepositoryPort
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
        self.participations[key] = participation

    async def list_by_trivia(self, trivia_id: UUID):
        return [
            p for (tid, _), p in self.participations.items() if tid == trivia_id
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
        # In tests, scores are already set correctly, so this is a no-op
        pass


@pytest.mark.asyncio
async def test_set_ready_success():
    """Test successful set ready."""
    # Setup
    trivia_id = uuid4()
    user_id = uuid4()
    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.LOBBY,
    )
    participation = Participation(
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.JOINED,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = participation

    use_case = SetReadyUseCase(trivia_repo, participation_repo)

    # Execute
    result = await use_case.execute(trivia_id, user_id)

    # Assert
    assert result.participation_id == participation.id
    assert result.participation_status == ParticipationStatus.READY

    # Verify participation was updated
    updated_participation = participation_repo.participations[(trivia_id, user_id)]
    assert updated_participation.status == ParticipationStatus.READY
    assert updated_participation.ready_at is not None


@pytest.mark.asyncio
async def test_set_ready_trivia_not_found():
    """Test set ready when trivia doesn't exist."""
    trivia_id = uuid4()
    user_id = uuid4()

    trivia_repo = InMemoryTriviaRepository()
    participation_repo = InMemoryParticipationRepository()

    use_case = SetReadyUseCase(trivia_repo, participation_repo)

    # Execute & Assert
    with pytest.raises(NotFoundError, match="Trivia .* not found"):
        await use_case.execute(trivia_id, user_id)


@pytest.mark.asyncio
async def test_set_ready_invalid_state():
    """Test set ready when trivia is not in LOBBY."""
    trivia_id = uuid4()
    user_id = uuid4()
    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,  # Not LOBBY
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()

    use_case = SetReadyUseCase(trivia_repo, participation_repo)

    # Execute & Assert
    with pytest.raises(InvalidStateError, match="Cannot set ready when trivia is in status"):
        await use_case.execute(trivia_id, user_id)


@pytest.mark.asyncio
async def test_set_ready_participation_not_found():
    """Test set ready when participation doesn't exist."""
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

    use_case = SetReadyUseCase(trivia_repo, participation_repo)

    # Execute & Assert
    with pytest.raises(NotFoundError, match="Participation not found"):
        await use_case.execute(trivia_id, user_id)

