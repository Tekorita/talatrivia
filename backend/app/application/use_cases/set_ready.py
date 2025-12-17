"""Set ready use case."""
from datetime import UTC, datetime
from uuid import UUID

from app.application.dtos.set_ready_dto import SetReadyDTO
from app.domain.entities.participation import ParticipationStatus
from app.domain.enums.trivia_status import TriviaStatus
from app.domain.errors import InvalidStateError, NotFoundError
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort


class SetReadyUseCase:
    """Use case for setting a participant as ready."""
    
    def __init__(
        self,
        trivia_repository: TriviaRepositoryPort,
        participation_repository: ParticipationRepositoryPort,
    ):
        self.trivia_repository = trivia_repository
        self.participation_repository = participation_repository
    
    async def execute(self, trivia_id: UUID, user_id: UUID) -> SetReadyDTO:
        """
        Execute set ready use case.
        
        Args:
            trivia_id: The trivia ID
            user_id: The user ID setting ready
            
        Returns:
            SetReadyDTO with updated participation status
            
        Raises:
            NotFoundError: If trivia or participation doesn't exist
            InvalidStateError: If trivia is not in LOBBY status
        """
        # Get trivia
        trivia = await self.trivia_repository.get_by_id(trivia_id)
        if not trivia:
            raise NotFoundError(f"Trivia {trivia_id} not found")
        
        # Check trivia is in LOBBY
        if trivia.status != TriviaStatus.LOBBY:
            raise InvalidStateError(
                f"Cannot set ready when trivia is in status {trivia.status.value}"
            )
        
        # Get participation
        participation = await self.participation_repository.get_by_trivia_and_user(
            trivia_id, user_id
        )
        if not participation:
            raise NotFoundError(
                f"Participation not found for trivia {trivia_id} and user {user_id}"
            )
        
        # Update participation status
        participation.status = ParticipationStatus.READY
        participation.ready_at = datetime.now(UTC)
        
        await self.participation_repository.update(participation)
        
        return SetReadyDTO(
            participation_id=participation.id,
            participation_status=participation.status,
        )

