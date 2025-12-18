"""Play router for players."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.admin_lobby_dtos import LobbyDTO
from app.application.use_cases.get_admin_lobby_use_case import GetAdminLobbyUseCase
from app.application.use_cases.get_assigned_trivias import (
    GetAssignedTriviasUseCase,
)
from app.application.use_cases.update_heartbeat import UpdateHeartbeatUseCase
from app.domain.errors import NotFoundError
from app.infrastructure.db.repositories import (
    SQLAlchemyParticipationRepository,
    SQLAlchemyTriviaRepository,
    SQLAlchemyUserRepository,
)
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/play/trivias", tags=["play"])


def get_get_admin_lobby_use_case(
    db: AsyncSession = Depends(get_db),
) -> GetAdminLobbyUseCase:
    """Dependency to get GetAdminLobbyUseCase."""
    trivia_repo = SQLAlchemyTriviaRepository(db)
    participation_repo = SQLAlchemyParticipationRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    return GetAdminLobbyUseCase(trivia_repo, participation_repo, user_repo)


def get_update_heartbeat_use_case(
    db: AsyncSession = Depends(get_db),
) -> UpdateHeartbeatUseCase:
    """Dependency to get UpdateHeartbeatUseCase."""
    trivia_repo = SQLAlchemyTriviaRepository(db)
    participation_repo = SQLAlchemyParticipationRepository(db)
    return UpdateHeartbeatUseCase(trivia_repo, participation_repo)


def get_get_assigned_trivias_use_case(
    db: AsyncSession = Depends(get_db),
) -> GetAssignedTriviasUseCase:
    """Dependency to get GetAssignedTriviasUseCase."""
    participation_repo = SQLAlchemyParticipationRepository(db)
    trivia_repo = SQLAlchemyTriviaRepository(db)
    return GetAssignedTriviasUseCase(participation_repo, trivia_repo)


class AssignedTriviaResponse(BaseModel):
    """Assigned trivia response."""
    trivia_id: str
    title: str
    description: str
    status: str


@router.get("/assigned", response_model=list[AssignedTriviaResponse])
async def get_assigned_trivias(
    user_id: UUID = Query(..., description="User ID to get assigned trivias for"),
    use_case: GetAssignedTriviasUseCase = Depends(get_get_assigned_trivias_use_case),
    # TODO: Add authentication to verify user role is PLAYER and user_id matches authenticated user
):
    """
    Get trivias assigned to a user.
    
    Args:
        user_id: The user ID (query parameter)
        use_case: Get assigned trivias use case
        
    Returns:
        List of assigned trivias with id, title, description, and status
    """
    trivias = await use_case.execute(user_id)
    return [
        {
            "trivia_id": str(trivia.trivia_id),
            "title": trivia.title,
            "description": trivia.description,
            "status": trivia.status,
        }
        for trivia in trivias
    ]


@router.get("/{trivia_id}/lobby", response_model=LobbyDTO)
async def get_player_lobby(
    trivia_id: UUID,
    use_case: GetAdminLobbyUseCase = Depends(get_get_admin_lobby_use_case),
    # TODO: Add authentication to verify user role is PLAYER
):
    """
    Get lobby information for players (read-only).
    
    Args:
        trivia_id: The trivia ID
        use_case: Get admin lobby use case (reused for player lobby)
        
    Returns:
        LobbyDTO with players list (name, present, ready status)
        
    Raises:
        HTTPException: 404 if trivia not found
    """
    try:
        result = await use_case.execute_for_player(trivia_id)
        return {
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


class HeartbeatRequest(BaseModel):
    """Heartbeat request."""
    user_id: UUID


@router.post("/{trivia_id}/heartbeat", status_code=status.HTTP_204_NO_CONTENT)
async def update_heartbeat(
    trivia_id: UUID,
    request: HeartbeatRequest,
    use_case: UpdateHeartbeatUseCase = Depends(get_update_heartbeat_use_case),
    # TODO: Add authentication to verify user role is PLAYER and user_id matches authenticated user
):
    """
    Update player heartbeat (last_seen_at).
    
    Args:
        trivia_id: The trivia ID
        request: Heartbeat request with user_id
        use_case: Update heartbeat use case
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: 404 if trivia or participation not found
    """
    try:
        await use_case.execute(trivia_id, request.user_id)
        return None
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
