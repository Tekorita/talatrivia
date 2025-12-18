"""Get admin lobby use case."""
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.application.dtos.admin_lobby_dtos import AdminLobbyDTO, LobbyDTO, LobbyPlayerDTO
from app.core.config import settings
from app.domain.entities.participation import ParticipationStatus
from app.domain.errors import NotFoundError
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort
from app.domain.ports.user_repository import UserRepositoryPort


class GetAdminLobbyUseCase:
    """Use case for getting admin lobby information."""
    
    def __init__(
        self,
        trivia_repository: TriviaRepositoryPort,
        participation_repository: ParticipationRepositoryPort,
        user_repository: UserRepositoryPort,
    ):
        self.trivia_repository = trivia_repository
        self.participation_repository = participation_repository
        self.user_repository = user_repository
    
    async def execute(self, trivia_id: UUID) -> AdminLobbyDTO:
        """
        Execute get admin lobby use case.
        
        Args:
            trivia_id: The trivia ID
            
        Returns:
            AdminLobbyDTO with assigned, present, ready counts and players list
            
        Raises:
            NotFoundError: If trivia doesn't exist
        """
        # Get trivia to verify it exists
        trivia = await self.trivia_repository.get_by_id(trivia_id)
        if not trivia:
            raise NotFoundError(f"Trivia {trivia_id} not found")
        
        # Get all participations for this trivia (these are the assigned players)
        participations = await self.participation_repository.list_by_trivia(trivia_id)
        
        assigned_count = len(participations)
        present_count = 0
        ready_count = 0
        players = []
        
        # Get user information for all participations - OPTIMIZED: single query instead of N queries
        user_ids = [p.user_id for p in participations]
        users_list = await self.user_repository.get_by_ids(user_ids)
        users_dict = {user.id: user for user in users_list}
        
        # Process each participation
        for participation in participations:
            user = users_dict.get(participation.user_id)
            if not user:
                continue  # Skip if user not found
            
            # Determine presence based on last_seen_at TTL
            # Note: participation.last_seen_at is naive (from DB), so we need to make now naive too
            now_naive = datetime.now(UTC).replace(tzinfo=None)
            presence_ttl = timedelta(seconds=settings.PRESENCE_TTL_SECONDS)
            present = (
                participation.last_seen_at is not None
                and (now_naive - participation.last_seen_at) <= presence_ttl
            )
            ready = participation.status == ParticipationStatus.READY
            
            if present:
                present_count += 1
            if ready:
                ready_count += 1
            
            players.append(
                LobbyPlayerDTO(
                    user_id=str(participation.user_id),
                    name=user.name,
                    present=present,
                    ready=ready,
                )
            )
        
        # Sort players by name ASC
        players.sort(key=lambda p: p.name)
        
        return AdminLobbyDTO(
            assigned_count=assigned_count,
            present_count=present_count,
            ready_count=ready_count,
            players=players,
        )
    
    async def execute_for_player(self, trivia_id: UUID) -> LobbyDTO:
        """
        Execute get lobby use case for players (returns only players list).
        
        Args:
            trivia_id: The trivia ID
            
        Returns:
            LobbyDTO with players list only
            
        Raises:
            NotFoundError: If trivia doesn't exist
        """
        admin_lobby = await self.execute(trivia_id)
        return LobbyDTO(players=admin_lobby.players)
