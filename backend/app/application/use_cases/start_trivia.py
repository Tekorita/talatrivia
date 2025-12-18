"""Start trivia use case."""
from datetime import UTC, datetime
from uuid import UUID

from app.application.dtos.start_trivia_dto import StartTriviaDTO
from app.domain.entities.participation import ParticipationStatus
from app.domain.enums.trivia_status import TriviaStatus
from app.domain.errors import ConflictError, ForbiddenError, InvalidStateError, NotFoundError
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort


class StartTriviaUseCase:
    """Use case for starting a trivia."""
    
    def __init__(
        self,
        trivia_repository: TriviaRepositoryPort,
        participation_repository: ParticipationRepositoryPort,
    ):
        self.trivia_repository = trivia_repository
        self.participation_repository = participation_repository
    
    async def execute(
        self,
        trivia_id: UUID,
        admin_user_id: UUID,
    ) -> StartTriviaDTO:
        """
        Execute start trivia use case.
        
        Args:
            trivia_id: The trivia ID to start
            admin_user_id: The admin user ID (must be creator)
            
        Returns:
            StartTriviaDTO with trivia status and timestamps
            
        Raises:
            NotFoundError: If trivia doesn't exist
            ForbiddenError: If user is not the creator
            InvalidStateError: If trivia is not in LOBBY or no ready players
        """
        # Get trivia
        trivia = await self.trivia_repository.get_by_id(trivia_id)
        if not trivia:
            raise NotFoundError(f"Trivia {trivia_id} not found")
        
        # Check user is creator
        if trivia.created_by_user_id != admin_user_id:
            raise ForbiddenError(
                f"User {admin_user_id} is not authorized to start trivia {trivia_id}"
            )
        
        # Check trivia is in LOBBY
        if trivia.status != TriviaStatus.LOBBY:
            raise InvalidStateError(
                f"Cannot start trivia in status {trivia.status.value}"
            )
        
        # Get all participations (assigned players)
        participations = await self.participation_repository.list_by_trivia(trivia_id)
        assigned_count = len(participations)
        
        if assigned_count == 0:
            raise InvalidStateError(
                "Cannot start trivia: no players assigned"
            )
        
        # Count present and ready players
        present_count = sum(1 for p in participations if p.joined_at is not None)
        ready_count = sum(
            1 for p in participations
            if p.status == ParticipationStatus.READY
        )
        
        # Validate all assigned players are present and ready
        if present_count != assigned_count:
            raise ConflictError(
                f"Cannot start trivia: {present_count} players present, but {assigned_count} assigned. "
                f"All assigned players must be present to start."
            )
        
        if ready_count != assigned_count:
            raise ConflictError(
                f"Cannot start trivia: {ready_count} players ready, but {assigned_count} assigned. "
                f"All assigned players must be ready to start."
            )
        
        # Update trivia status
        now = datetime.now(UTC)
        trivia.status = TriviaStatus.IN_PROGRESS
        trivia.started_at = now
        trivia.current_question_index = 0
        trivia.question_started_at = now
        
        await self.trivia_repository.update(trivia)
        
        return StartTriviaDTO(
            trivia_id=trivia_id,
            trivia_status=trivia.status,
            started_at=trivia.started_at,
            current_question_index=trivia.current_question_index,
        )

