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
from app.domain.errors import (
    ForbiddenError,
    InvalidStateError,
    NotFoundError,
)
from app.infrastructure.db.repositories import (
    SQLAlchemyParticipationRepository,
    SQLAlchemyTriviaRepository,
)
from app.infrastructure.db.session import get_db

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


@router.post("/{trivia_id}/ready")
async def set_ready(
    trivia_id: UUID,
    request: SetReadyRequest,
    use_case: SetReadyUseCase = Depends(get_set_ready_use_case),
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
    except InvalidStateError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

