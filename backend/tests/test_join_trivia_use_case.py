"""Tests for JoinTriviaUseCase."""
from uuid import UUID, uuid4

import pytest

from app.application.use_cases.join_trivia import JoinTriviaUseCase
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
        # In tests, scores are already set correctly, so this is a no-op
        pass


@pytest.mark.asyncio
async def test_join_trivia_success():
    """Test successful trivia join."""
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
    
    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia
    
    participation_repo = InMemoryParticipationRepository()
    
    use_case = JoinTriviaUseCase(trivia_repo, participation_repo)
    
    # Execute
    result = await use_case.execute(trivia_id, user_id)
    
    # Assert
    assert result.trivia_id == trivia_id
    assert result.participation_status == ParticipationStatus.READY
    assert result.trivia_status == TriviaStatus.LOBBY


@pytest.mark.asyncio
async def test_join_trivia_not_found():
    """Test join trivia when trivia doesn't exist."""
    trivia_id = uuid4()
    user_id = uuid4()
    
    trivia_repo = InMemoryTriviaRepository()
    participation_repo = InMemoryParticipationRepository()
    
    use_case = JoinTriviaUseCase(trivia_repo, participation_repo)
    
    # Execute & Assert
    with pytest.raises(NotFoundError):
        await use_case.execute(trivia_id, user_id)


@pytest.mark.asyncio
async def test_join_trivia_invalid_state():
    """Test join trivia when trivia is in invalid state."""
    trivia_id = uuid4()
    user_id = uuid4()
    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
    )
    
    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia
    
    participation_repo = InMemoryParticipationRepository()
    
    use_case = JoinTriviaUseCase(trivia_repo, participation_repo)
    
    # Execute & Assert
    with pytest.raises(InvalidStateError):
        await use_case.execute(trivia_id, user_id)


@pytest.mark.asyncio
async def test_join_trivia_idempotent_existing_joined():
    """Test join trivia when participation already exists and is JOINED (idempotent)."""
    trivia_id = uuid4()
    user_id = uuid4()
    participation_id = uuid4()
    
    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.LOBBY,
    )
    
    existing_participation = Participation(
        id=participation_id,
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.JOINED,
    )
    
    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia
    
    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = existing_participation
    
    use_case = JoinTriviaUseCase(trivia_repo, participation_repo)
    
    # Execute
    result = await use_case.execute(trivia_id, user_id)
    
    # Assert - should return existing participation (now updated to READY)
    assert result.participation_id == participation_id
    assert result.participation_status == ParticipationStatus.READY
    assert result.trivia_status == TriviaStatus.LOBBY


@pytest.mark.asyncio
async def test_join_trivia_idempotent_existing_ready():
    """Test join trivia when participation already exists and is READY (idempotent)."""
    trivia_id = uuid4()
    user_id = uuid4()
    participation_id = uuid4()
    
    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.LOBBY,
    )
    
    existing_participation = Participation(
        id=participation_id,
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.READY,
    )
    
    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia
    
    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[(trivia_id, user_id)] = existing_participation
    
    use_case = JoinTriviaUseCase(trivia_repo, participation_repo)
    
    # Execute
    result = await use_case.execute(trivia_id, user_id)
    
    # Assert - should return existing participation
    assert result.participation_id == participation_id
    assert result.participation_status == ParticipationStatus.READY


@pytest.mark.asyncio
async def test_join_trivia_draft_transitions_to_lobby():
    """Test join trivia when trivia is DRAFT transitions to LOBBY."""
    trivia_id = uuid4()
    user_id = uuid4()
    
    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.DRAFT,  # DRAFT status
    )
    
    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia
    
    participation_repo = InMemoryParticipationRepository()
    
    use_case = JoinTriviaUseCase(trivia_repo, participation_repo)
    
    # Execute
    result = await use_case.execute(trivia_id, user_id)
    
    # Assert
    assert result.trivia_id == trivia_id
    assert result.participation_status == ParticipationStatus.READY
    assert result.trivia_status == TriviaStatus.LOBBY  # Should be LOBBY now
    
    # Verify trivia was updated
    updated_trivia = trivia_repo.trivias[trivia_id]
    assert updated_trivia.status == TriviaStatus.LOBBY

