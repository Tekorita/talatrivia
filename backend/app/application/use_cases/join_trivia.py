"""Join trivia use case."""
import uuid
from datetime import UTC, datetime
from uuid import UUID

from app.application.dtos.join_trivia_dto import JoinTriviaDTO
from app.domain.entities.participation import Participation, ParticipationStatus
from app.domain.enums.trivia_status import TriviaStatus
from app.domain.errors import InvalidStateError, NotFoundError
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort


class JoinTriviaUseCase:
    """Use case for joining a trivia."""
    
    def __init__(
        self,
        trivia_repository: TriviaRepositoryPort,
        participation_repository: ParticipationRepositoryPort,
    ):
        self.trivia_repository = trivia_repository
        self.participation_repository = participation_repository
    
    async def execute(self, trivia_id: UUID, user_id: UUID) -> JoinTriviaDTO:
        """
        Execute join trivia use case.
        
        Args:
            trivia_id: The trivia ID to join
            user_id: The user ID joining
            
        Returns:
            JoinTriviaDTO with participation and trivia status
            
        Raises:
            NotFoundError: If trivia doesn't exist
            InvalidStateError: If trivia status doesn't allow joining
        """
        # Get trivia
        trivia = await self.trivia_repository.get_by_id(trivia_id)
        if not trivia:
            raise NotFoundError(f"Trivia {trivia_id} not found")
        
        # Check if trivia status allows joining
        if trivia.status not in [TriviaStatus.DRAFT, TriviaStatus.LOBBY]:
            raise InvalidStateError(
                f"Cannot join trivia in status {trivia.status.value}"
            )
        
        # Check if participation already exists
        existing_participation = await self.participation_repository.get_by_trivia_and_user(
            trivia_id, user_id
        )
        
        if existing_participation:
            # Idempotent: return existing participation if already joined/ready
            if existing_participation.status in [
                ParticipationStatus.INVITED,
                ParticipationStatus.JOINED,
                ParticipationStatus.READY,
            ]:
                return JoinTriviaDTO(
                    trivia_id=trivia_id,
                    participation_id=existing_participation.id,
                    participation_status=existing_participation.status,
                    trivia_status=trivia.status,
                )
        
        # If trivia is DRAFT, transition to LOBBY
        if trivia.status == TriviaStatus.DRAFT:
            trivia.status = TriviaStatus.LOBBY
            await self.trivia_repository.update(trivia)
        
        # Create new participation
        participation = Participation(
            id=uuid.uuid4(),  # Generate UUID
            trivia_id=trivia_id,
            user_id=user_id,
            status=ParticipationStatus.JOINED,
            joined_at=datetime.now(UTC),
        )
        
        created_participation = await self.participation_repository.create(participation)
        
        return JoinTriviaDTO(
            trivia_id=trivia_id,
            participation_id=created_participation.id,
            participation_status=created_participation.status,
            trivia_status=trivia.status,
        )

