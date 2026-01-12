"""Lobby router."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases import (
    JoinTriviaUseCase,
    SetReadyUseCase,
    StartTriviaUseCase,
)
from app.application.use_cases.get_admin_lobby_use_case import GetAdminLobbyUseCase
from app.application.use_cases.get_current_question import GetCurrentQuestionUseCase
from app.application.use_cases.get_trivia_ranking import GetTriviaRankingUseCase
from app.domain.errors import (
    ConflictError,
    ForbiddenError,
    InvalidStateError,
    NotFoundError,
)
from app.infrastructure.db.repositories import (
    SQLAlchemyOptionRepository,
    SQLAlchemyParticipationRepository,
    SQLAlchemyQuestionRepository,
    SQLAlchemyTriviaQuestionRepository,
    SQLAlchemyTriviaRepository,
    SQLAlchemyUserRepository,
)
from app.infrastructure.db.session import get_db
from app.infrastructure.sse.event_emitter import (
    emit_admin_lobby_updated,
    emit_current_question_updated,
    emit_lobby_updated,
    emit_ranking_updated,
    emit_status_updated,
)

router = APIRouter(prefix="/trivias", tags=["lobby"])


class JoinTriviaRequest(BaseModel):
    """Join trivia request."""
    user_id: UUID


class SetReadyRequest(BaseModel):
    """Set ready request."""
    user_id: UUID


class StartTriviaRequest(BaseModel):
    """Start trivia request."""
    admin_user_id: UUID


def get_join_trivia_use_case(
    db: AsyncSession = Depends(get_db),
) -> JoinTriviaUseCase:
    """Dependency to get JoinTriviaUseCase."""
    trivia_repo = SQLAlchemyTriviaRepository(db)
    participation_repo = SQLAlchemyParticipationRepository(db)
    return JoinTriviaUseCase(trivia_repo, participation_repo)


def get_set_ready_use_case(
    db: AsyncSession = Depends(get_db),
) -> SetReadyUseCase:
    """Dependency to get SetReadyUseCase."""
    trivia_repo = SQLAlchemyTriviaRepository(db)
    participation_repo = SQLAlchemyParticipationRepository(db)
    return SetReadyUseCase(trivia_repo, participation_repo)


def get_start_trivia_use_case(
    db: AsyncSession = Depends(get_db),
) -> StartTriviaUseCase:
    """Dependency to get StartTriviaUseCase."""
    trivia_repo = SQLAlchemyTriviaRepository(db)
    participation_repo = SQLAlchemyParticipationRepository(db)
    return StartTriviaUseCase(trivia_repo, participation_repo)


@router.post("/{trivia_id}/join")
async def join_trivia(
    trivia_id: UUID,
    request: JoinTriviaRequest,
    use_case: JoinTriviaUseCase = Depends(get_join_trivia_use_case),
    db: AsyncSession = Depends(get_db),
):
    """
    Join a trivia.
    
    Args:
        trivia_id: The trivia ID to join
        request: Join request with user_id
        use_case: Join trivia use case
        
    Returns:
        Join trivia response DTO
    """
    try:
        result = await use_case.execute(trivia_id, request.user_id)
        
        # Emit SSE events after successful join
        # Get lobby data for events
        trivia_repo = SQLAlchemyTriviaRepository(db)
        participation_repo = SQLAlchemyParticipationRepository(db)
        user_repo = SQLAlchemyUserRepository(db)
        get_lobby_use_case = GetAdminLobbyUseCase(trivia_repo, participation_repo, user_repo)
        
        lobby_dto = await get_lobby_use_case.execute_for_player(trivia_id)
        admin_lobby_dto = await get_lobby_use_case.execute(trivia_id)
        
        # Get trivia for status
        trivia = await trivia_repo.get_by_id(trivia_id)
        
        # Emit events
        await emit_lobby_updated(trivia_id, lobby_dto)
        await emit_admin_lobby_updated(trivia_id, admin_lobby_dto)
        await emit_status_updated(trivia_id, result.trivia_status.value, trivia.current_question_index if trivia else 0)
        
        return {
            "trivia_id": str(result.trivia_id),
            "participation_id": str(result.participation_id),
            "participation_status": result.participation_status.value,
            "trivia_status": result.trivia_status.value,
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except InvalidStateError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        # Catch any other unexpected errors
        import traceback
        error_detail = f"Internal server error: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        ) from e


@router.post("/{trivia_id}/ready")
async def set_ready(
    trivia_id: UUID,
    request: SetReadyRequest,
    use_case: SetReadyUseCase = Depends(get_set_ready_use_case),
    db: AsyncSession = Depends(get_db),
):
    """
    Set participant as ready.
    
    Args:
        trivia_id: The trivia ID
        request: Set ready request with user_id
        use_case: Set ready use case
        
    Returns:
        Set ready response DTO
    """
    try:
        result = await use_case.execute(trivia_id, request.user_id)
        
        # Emit SSE events after successful set ready
        trivia_repo = SQLAlchemyTriviaRepository(db)
        participation_repo = SQLAlchemyParticipationRepository(db)
        user_repo = SQLAlchemyUserRepository(db)
        get_lobby_use_case = GetAdminLobbyUseCase(trivia_repo, participation_repo, user_repo)
        
        lobby_dto = await get_lobby_use_case.execute_for_player(trivia_id)
        admin_lobby_dto = await get_lobby_use_case.execute(trivia_id)
        
        # Get trivia for status
        trivia = await trivia_repo.get_by_id(trivia_id)
        
        # Emit events
        await emit_lobby_updated(trivia_id, lobby_dto)
        await emit_admin_lobby_updated(trivia_id, admin_lobby_dto)
        await emit_status_updated(trivia_id, trivia.status.value if trivia else "LOBBY", trivia.current_question_index if trivia else 0)
        
        return {
            "participation_id": str(result.participation_id),
            "participation_status": result.participation_status.value,
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except InvalidStateError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@router.post("/{trivia_id}/start")
async def start_trivia(
    trivia_id: UUID,
    request: StartTriviaRequest,
    use_case: StartTriviaUseCase = Depends(get_start_trivia_use_case),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a trivia.
    
    Args:
        trivia_id: The trivia ID to start
        request: Start request with admin_user_id
        use_case: Start trivia use case
        
    Returns:
        Start trivia response DTO
    """
    try:
        result = await use_case.execute(trivia_id, request.admin_user_id)
        
        # Emit SSE events after successful start
        trivia_repo = SQLAlchemyTriviaRepository(db)
        participation_repo = SQLAlchemyParticipationRepository(db)
        user_repo = SQLAlchemyUserRepository(db)
        trivia_question_repo = SQLAlchemyTriviaQuestionRepository(db)
        question_repo = SQLAlchemyQuestionRepository(db)
        option_repo = SQLAlchemyOptionRepository(db)
        
        # Emit status update
        await emit_status_updated(trivia_id, result.trivia_status.value, result.current_question_index)
        
        # Emit current question if trivia is IN_PROGRESS
        if result.trivia_status.value == "IN_PROGRESS":
            get_current_question_use_case = GetCurrentQuestionUseCase(
                trivia_repo, participation_repo, trivia_question_repo, question_repo, option_repo
            )
            # Get first participant for current question (any user_id works for getting question)
            participations = await participation_repo.list_by_trivia(trivia_id)
            if participations:
                current_question_dto = await get_current_question_use_case.execute(
                    trivia_id, participations[0].user_id
                )
                await emit_current_question_updated(trivia_id, current_question_dto)
        
        # Emit ranking update
        get_ranking_use_case = GetTriviaRankingUseCase(trivia_repo, participation_repo, user_repo)
        ranking_dto = await get_ranking_use_case.execute(trivia_id)
        await emit_ranking_updated(trivia_id, ranking_dto)
        
        return {
            "trivia_id": str(result.trivia_id),
            "trivia_status": result.trivia_status.value,
            "started_at": result.started_at.isoformat(),
            "current_question_index": result.current_question_index,
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
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
    except Exception as e:
        # Catch any other unexpected errors
        import traceback
        error_detail = f"Internal server error: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        ) from e

