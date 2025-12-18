"""Admin router."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.admin_lobby_dtos import AdminLobbyDTO
from app.application.use_cases.get_admin_lobby_use_case import GetAdminLobbyUseCase
from app.domain.errors import NotFoundError
from app.infrastructure.db.repositories import (
    SQLAlchemyParticipationRepository,
    SQLAlchemyTriviaRepository,
    SQLAlchemyUserRepository,
)
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/admin/trivias", tags=["admin"])


def get_get_admin_lobby_use_case(
    db: AsyncSession = Depends(get_db),
) -> GetAdminLobbyUseCase:
    """Dependency to get GetAdminLobbyUseCase."""
    trivia_repo = SQLAlchemyTriviaRepository(db)
    participation_repo = SQLAlchemyParticipationRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    return GetAdminLobbyUseCase(trivia_repo, participation_repo, user_repo)


@router.get("/{trivia_id}/lobby", response_model=AdminLobbyDTO)
async def get_admin_lobby(
    trivia_id: UUID,
    use_case: GetAdminLobbyUseCase = Depends(get_get_admin_lobby_use_case),
):
    """
    Get admin lobby information for a trivia.
    
    Args:
        trivia_id: The trivia ID
        use_case: Get admin lobby use case
        
    Returns:
        AdminLobbyDTO with assigned, present, ready counts and players list
        
    Raises:
        HTTPException: 404 if trivia not found
    """
    try:
        result = await use_case.execute(trivia_id)
        return {
            "assigned_count": result.assigned_count,
            "present_count": result.present_count,
            "ready_count": result.ready_count,
            "players": [
                {
                    "user_id": player.user_id,
                    "name": player.name,
                    "present": player.present,
                    "ready": player.ready,
                }
                for player in result.players
            ],
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
