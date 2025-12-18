"""Get assigned trivias use case."""
from typing import List
from uuid import UUID

from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort


class AssignedTriviaDTO:
    """DTO for assigned trivia."""
    def __init__(self, trivia_id: UUID, title: str, description: str, status: str):
        self.trivia_id = trivia_id
        self.title = title
        self.description = description
        self.status = status


class GetAssignedTriviasUseCase:
    """Use case for getting trivias assigned to a user."""
    
    def __init__(
        self,
        participation_repository: ParticipationRepositoryPort,
        trivia_repository: TriviaRepositoryPort,
    ):
        self.participation_repository = participation_repository
        self.trivia_repository = trivia_repository
    
    async def execute(self, user_id: UUID) -> List[AssignedTriviaDTO]:
        """
        Execute get assigned trivias use case.
        
        Args:
            user_id: The user ID
            
        Returns:
            List of AssignedTriviaDTO with trivia information
        """
        # Get all participations for this user
        participations = await self.participation_repository.list_by_user(user_id)
        
        # Get trivia details for each participation
        trivias = []
        for participation in participations:
            trivia = await self.trivia_repository.get_by_id(participation.trivia_id)
            if trivia:
                trivias.append(
                    AssignedTriviaDTO(
                        trivia_id=trivia.id,
                        title=trivia.title,
                        description=trivia.description,
                        status=trivia.status.value,
                    )
                )
        
        return trivias
