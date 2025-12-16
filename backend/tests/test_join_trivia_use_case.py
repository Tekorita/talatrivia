"""Tests for JoinTriviaUseCase."""
import pytest
from uuid import UUID, uuid4
from app.application.use_cases.join_trivia import JoinTriviaUseCase
from app.domain.entities.trivia import Trivia, TriviaStatus
from app.domain.entities.participation import Participation, ParticipationStatus
from app.domain.ports.trivia_repository import TriviaRepositoryPort
from app.domain.ports.participation_repository import ParticipationRepositoryPort
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
    assert result.participation_status == ParticipationStatus.JOINED
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

