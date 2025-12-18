"""Get trivia ranking use case."""
from uuid import UUID

from app.application.dtos.trivia_ranking_dto import RankingEntryDTO, TriviaRankingDTO
from app.domain.errors import NotFoundError
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort
from app.domain.ports.user_repository import UserRepositoryPort


class GetTriviaRankingUseCase:
    """Use case for getting the ranking of a trivia."""

    def __init__(
        self,
        trivia_repository: TriviaRepositoryPort,
        participation_repository: ParticipationRepositoryPort,
        user_repository: UserRepositoryPort,
    ):
        self.trivia_repository = trivia_repository
        self.participation_repository = participation_repository
        self.user_repository = user_repository

    async def execute(self, trivia_id: UUID) -> TriviaRankingDTO:
        """
        Execute get trivia ranking use case.

        Args:
            trivia_id: The trivia ID

        Returns:
            TriviaRankingDTO with ranking ordered by score DESC

        Raises:
            NotFoundError: If trivia doesn't exist
        """
        # Get trivia to verify it exists and get status
        trivia = await self.trivia_repository.get_by_id(trivia_id)
        if not trivia:
            raise NotFoundError(f"Trivia {trivia_id} not found")

        # Ensure scores are consistent before reading ranking
        await self.participation_repository.recompute_scores_for_trivia(trivia_id)

        # Get all participations for the trivia (already ordered by score DESC from repository)
        participations = await self.participation_repository.list_by_trivia(trivia_id)

        # If no participations, return empty ranking
        if not participations:
            return TriviaRankingDTO(
                trivia_id=trivia_id,
                status=trivia.status,
                ranking=[],
            )

        # Get users for all participations - OPTIMIZED: single query instead of N queries
        user_ids = list({p.user_id for p in participations})
        users_list = await self.user_repository.get_by_ids(user_ids)
        users = {user.id: user for user in users_list}

        # Build ranking entries with positions
        ranking_entries = []
        for position, participation in enumerate(participations, start=1):
            user = users.get(participation.user_id)
            if user:
                ranking_entries.append(
                    RankingEntryDTO(
                        position=position,
                        user_id=participation.user_id,
                        user_name=user.name,
                        score=participation.score,
                    )
                )

        return TriviaRankingDTO(
            trivia_id=trivia_id,
            status=trivia.status,
            ranking=ranking_entries,
        )

