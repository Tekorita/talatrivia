"""Tests for GetTriviaRankingUseCase."""
from typing import Dict, List
from uuid import UUID, uuid4

import pytest

from app.application.use_cases.get_trivia_ranking import GetTriviaRankingUseCase
from app.domain.entities.participation import Participation, ParticipationStatus
from app.domain.entities.trivia import Trivia, TriviaStatus
from app.domain.entities.user import User
from app.domain.errors import NotFoundError
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort
from app.domain.ports.user_repository import UserRepositoryPort


class InMemoryTriviaRepository(TriviaRepositoryPort):
    """In-memory trivia repository for testing."""

    def __init__(self):
        self.trivias: Dict[UUID, Trivia] = {}

    async def get_by_id(self, trivia_id: UUID) -> Trivia | None:
        return self.trivias.get(trivia_id)

    async def update(self, trivia: Trivia) -> None:
        self.trivias[trivia.id] = trivia


class InMemoryParticipationRepository(ParticipationRepositoryPort):
    """In-memory participation repository for testing."""

    def __init__(self):
        self.participations: Dict[UUID, Participation] = {}

    async def get_by_trivia_and_user(
        self, trivia_id: UUID, user_id: UUID
    ) -> Participation | None:
        return next(
            (
                p
                for p in self.participations.values()
                if p.trivia_id == trivia_id and p.user_id == user_id
            ),
            None,
        )

    async def create(self, participation: Participation) -> Participation:
        self.participations[participation.id] = participation
        return participation

    async def update(self, participation: Participation) -> None:
        self.participations[participation.id] = participation

    async def list_by_trivia(self, trivia_id: UUID) -> List[Participation]:
        participations = [
            p for p in self.participations.values() if p.trivia_id == trivia_id
        ]
        # Sort by score DESC (simulating repository behavior)
        return sorted(participations, key=lambda p: p.score, reverse=True)


class InMemoryUserRepository(UserRepositoryPort):
    """In-memory user repository for testing."""

    def __init__(self):
        self.users: Dict[UUID, User] = {}

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.users.get(user_id)
    
    async def get_by_email(self, email: str) -> User | None:
        for user in self.users.values():
            if user.email == email:
                return user
        return None


@pytest.mark.asyncio
async def test_get_trivia_ranking_success():
    """Test successful ranking retrieval."""
    # Setup
    trivia_id = uuid4()
    user_id_1 = uuid4()
    user_id_2 = uuid4()
    user_id_3 = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
    )

    user_1 = User(
        id=user_id_1,
        name="Alice",
        email="alice@test.com",
        password_hash="hash1",
    )
    user_2 = User(
        id=user_id_2,
        name="Bob",
        email="bob@test.com",
        password_hash="hash2",
    )
    user_3 = User(
        id=user_id_3,
        name="Charlie",
        email="charlie@test.com",
        password_hash="hash3",
    )

    participation_1 = Participation(
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id_1,
        status=ParticipationStatus.READY,
        score=100,
    )
    participation_2 = Participation(
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id_2,
        status=ParticipationStatus.READY,
        score=150,  # Highest score
    )
    participation_3 = Participation(
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id_3,
        status=ParticipationStatus.READY,
        score=50,  # Lowest score
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[participation_1.id] = participation_1
    participation_repo.participations[participation_2.id] = participation_2
    participation_repo.participations[participation_3.id] = participation_3

    user_repo = InMemoryUserRepository()
    user_repo.users[user_id_1] = user_1
    user_repo.users[user_id_2] = user_2
    user_repo.users[user_id_3] = user_3

    use_case = GetTriviaRankingUseCase(trivia_repo, participation_repo, user_repo)

    # Execute
    result = await use_case.execute(trivia_id)

    # Assert
    assert result.trivia_id == trivia_id
    assert result.status == TriviaStatus.IN_PROGRESS
    assert len(result.ranking) == 3

    # Check ranking order (should be sorted by score DESC)
    assert result.ranking[0].position == 1
    assert result.ranking[0].user_id == user_id_2
    assert result.ranking[0].user_name == "Bob"
    assert result.ranking[0].score == 150

    assert result.ranking[1].position == 2
    assert result.ranking[1].user_id == user_id_1
    assert result.ranking[1].user_name == "Alice"
    assert result.ranking[1].score == 100

    assert result.ranking[2].position == 3
    assert result.ranking[2].user_id == user_id_3
    assert result.ranking[2].user_name == "Charlie"
    assert result.ranking[2].score == 50


@pytest.mark.asyncio
async def test_get_trivia_ranking_empty():
    """Test ranking when no participations exist."""
    # Setup
    trivia_id = uuid4()
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
    user_repo = InMemoryUserRepository()

    use_case = GetTriviaRankingUseCase(trivia_repo, participation_repo, user_repo)

    # Execute
    result = await use_case.execute(trivia_id)

    # Assert
    assert result.trivia_id == trivia_id
    assert result.status == TriviaStatus.IN_PROGRESS
    assert len(result.ranking) == 0


@pytest.mark.asyncio
async def test_get_trivia_ranking_not_found():
    """Test ranking when trivia doesn't exist."""
    trivia_id = uuid4()

    trivia_repo = InMemoryTriviaRepository()
    participation_repo = InMemoryParticipationRepository()
    user_repo = InMemoryUserRepository()

    use_case = GetTriviaRankingUseCase(trivia_repo, participation_repo, user_repo)

    # Execute & Assert
    with pytest.raises(NotFoundError, match="Trivia .* not found"):
        await use_case.execute(trivia_id)


@pytest.mark.asyncio
async def test_get_trivia_ranking_finished_status():
    """Test ranking when trivia is finished."""
    # Setup
    trivia_id = uuid4()
    user_id = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.FINISHED,
    )

    user = User(
        id=user_id,
        name="Alice",
        email="alice@test.com",
        password_hash="hash1",
    )

    participation = Participation(
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id,
        status=ParticipationStatus.FINISHED,
        score=100,
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[participation.id] = participation

    user_repo = InMemoryUserRepository()
    user_repo.users[user_id] = user

    use_case = GetTriviaRankingUseCase(trivia_repo, participation_repo, user_repo)

    # Execute
    result = await use_case.execute(trivia_id)

    # Assert
    assert result.trivia_id == trivia_id
    assert result.status == TriviaStatus.FINISHED
    assert len(result.ranking) == 1
    assert result.ranking[0].position == 1
    assert result.ranking[0].score == 100


@pytest.mark.asyncio
async def test_get_trivia_ranking_reflects_current_scores():
    """Test that ranking reflects current scores (simulating score changes)."""
    # Setup
    trivia_id = uuid4()
    user_id_1 = uuid4()
    user_id_2 = uuid4()

    trivia = Trivia(
        id=trivia_id,
        title="Test Trivia",
        description="Test Description",
        created_by_user_id=uuid4(),
        status=TriviaStatus.IN_PROGRESS,
    )

    user_1 = User(
        id=user_id_1,
        name="Alice",
        email="alice@test.com",
        password_hash="hash1",
    )
    user_2 = User(
        id=user_id_2,
        name="Bob",
        email="bob@test.com",
        password_hash="hash2",
    )

    participation_1 = Participation(
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id_1,
        status=ParticipationStatus.READY,
        score=50,  # Initially lower
    )
    participation_2 = Participation(
        id=uuid4(),
        trivia_id=trivia_id,
        user_id=user_id_2,
        status=ParticipationStatus.READY,
        score=100,  # Initially higher
    )

    trivia_repo = InMemoryTriviaRepository()
    trivia_repo.trivias[trivia_id] = trivia

    participation_repo = InMemoryParticipationRepository()
    participation_repo.participations[participation_1.id] = participation_1
    participation_repo.participations[participation_2.id] = participation_2

    user_repo = InMemoryUserRepository()
    user_repo.users[user_id_1] = user_1
    user_repo.users[user_id_2] = user_2

    use_case = GetTriviaRankingUseCase(trivia_repo, participation_repo, user_repo)

    # Execute first ranking
    result_1 = await use_case.execute(trivia_id)
    assert result_1.ranking[0].user_id == user_id_2  # Bob first
    assert result_1.ranking[1].user_id == user_id_1  # Alice second

    # Simulate score change (Alice answers correctly, gets more points)
    participation_1.score = 150
    participation_repo.participations[participation_1.id] = participation_1

    # Execute second ranking
    result_2 = await use_case.execute(trivia_id)
    assert result_2.ranking[0].user_id == user_id_1  # Alice first now
    assert result_2.ranking[1].user_id == user_id_2  # Bob second now
    assert result_2.ranking[0].score == 150
    assert result_2.ranking[1].score == 100

