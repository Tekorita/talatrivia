"""Update heartbeat use case."""
from datetime import UTC, datetime
from uuid import UUID

from app.domain.errors import NotFoundError
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort


class UpdateHeartbeatUseCase:
    """Use case for updating player heartbeat (last_seen_at)."""
    
    def __init__(
        self,
        trivia_repository: TriviaRepositoryPort,
        participation_repository: ParticipationRepositoryPort,
    ):
        self.trivia_repository = trivia_repository
        self.participation_repository = participation_repository
    
    async def execute(self, trivia_id: UUID, user_id: UUID) -> None:
        """
        Execute update heartbeat use case.
        
        Args:
            trivia_id: The trivia ID
            user_id: The user ID to update heartbeat for
            
        Raises:
            NotFoundError: If trivia or participation doesn't exist
        """
        # Verify trivia exists
        trivia = await self.trivia_repository.get_by_id(trivia_id)
        if not trivia:
            raise NotFoundError(f"Trivia {trivia_id} not found")
        
        # Get participation
        participation = await self.participation_repository.get_by_trivia_and_user(
            trivia_id, user_id
        )
        if not participation:
            raise NotFoundError(
                f"Participation not found for trivia {trivia_id} and user {user_id}"
            )
        
        # Update last_seen_at
        participation.last_seen_at = datetime.now(UTC)
        await self.participation_repository.update(participation)
