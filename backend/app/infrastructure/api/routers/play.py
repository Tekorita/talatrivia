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
from app.application.use_cases.use_fifty_fifty_lifeline import UseFiftyFiftyLifelineUseCase
from app.domain.errors import ConflictError, InvalidStateError, NotFoundError
from app.infrastructure.db.repositories import (
    SQLAlchemyAnswerRepository,
    SQLAlchemyOptionRepository,
    SQLAlchemyParticipationRepository,
    SQLAlchemyQuestionRepository,
    SQLAlchemyTriviaQuestionRepository,
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


class UseFiftyFiftyRequest(BaseModel):
    """Use fifty-fifty lifeline request."""
    user_id: UUID


def get_use_fifty_fifty_lifeline_use_case(
    db: AsyncSession = Depends(get_db),
) -> UseFiftyFiftyLifelineUseCase:
    """Dependency to get UseFiftyFiftyLifelineUseCase."""
    trivia_repo = SQLAlchemyTriviaRepository(db)
    participation_repo = SQLAlchemyParticipationRepository(db)
    trivia_question_repo = SQLAlchemyTriviaQuestionRepository(db)
    question_repo = SQLAlchemyQuestionRepository(db)
    option_repo = SQLAlchemyOptionRepository(db)
    answer_repo = SQLAlchemyAnswerRepository(db)
    return UseFiftyFiftyLifelineUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )


@router.post("/{trivia_id}/questions/{question_id}/lifelines/50-50")
async def use_fifty_fifty_lifeline(
    trivia_id: UUID,
    question_id: UUID,
    request: UseFiftyFiftyRequest,
    use_case: UseFiftyFiftyLifelineUseCase = Depends(get_use_fifty_fifty_lifeline_use_case),
    # TODO: Add authentication to verify user role is PLAYER and user_id matches authenticated user
):
    """
    Use the 50/50 lifeline for a question.
    
    Args:
        trivia_id: The trivia ID
        question_id: The question ID
        request: Use fifty-fifty request with user_id
        use_case: Use fifty-fifty lifeline use case
        
    Returns:
        UseFiftyFiftyResultDTO with 2 allowed options (1 correct + 1 incorrect)
        
    Raises:
        HTTPException: 404 if trivia, participation, or question not found
        HTTPException: 403 if user not assigned to trivia
        HTTPException: 409 if lifeline already used or question already answered
        HTTPException: 422 if trivia is not in IN_PROGRESS or invalid state
    """
    try:
        result = await use_case.execute(trivia_id, question_id, request.user_id)
        return {
            "allowed_options": [
                {
                    "id": str(opt.id),
                    "text": opt.text,
                }
                for opt in result.allowed_options
            ],
            "fifty_fifty_used": result.fifty_fifty_used,
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except InvalidStateError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


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
