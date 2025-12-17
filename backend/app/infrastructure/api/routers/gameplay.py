"""Gameplay router."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.advance_question import AdvanceQuestionUseCase
from app.application.use_cases.get_current_question import GetCurrentQuestionUseCase
from app.application.use_cases.get_trivia_ranking import GetTriviaRankingUseCase
from app.application.use_cases.submit_answer import SubmitAnswerUseCase
from app.domain.errors import ConflictError, ForbiddenError, InvalidStateError, NotFoundError
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

router = APIRouter(prefix="/trivias", tags=["gameplay"])


class SubmitAnswerRequest(BaseModel):
    """Submit answer request."""
    user_id: UUID
    selected_option_id: UUID


class AdvanceQuestionRequest(BaseModel):
    """Advance question request."""
    admin_user_id: UUID


def get_get_current_question_use_case(
    db: AsyncSession = Depends(get_db),
) -> GetCurrentQuestionUseCase:
    """Dependency to get GetCurrentQuestionUseCase."""
    trivia_repo = SQLAlchemyTriviaRepository(db)
    participation_repo = SQLAlchemyParticipationRepository(db)
    trivia_question_repo = SQLAlchemyTriviaQuestionRepository(db)
    question_repo = SQLAlchemyQuestionRepository(db)
    option_repo = SQLAlchemyOptionRepository(db)
    return GetCurrentQuestionUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
    )


@router.get("/{trivia_id}/current-question")
async def get_current_question(
    trivia_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    use_case: GetCurrentQuestionUseCase = Depends(get_get_current_question_use_case),
):
    """
    Get the current question of a trivia in progress.

    Args:
        trivia_id: The trivia ID
        user_id: The user ID (query parameter)
        use_case: Get current question use case

    Returns:
        Current question DTO with options (without correct answer)
    """
    try:
        result = await use_case.execute(trivia_id, user_id)
        return {
            "question_id": str(result.question_id),
            "question_text": result.question_text,
            "options": [
                {
                    "option_id": str(opt.option_id),
                    "option_text": opt.option_text,
                }
                for opt in result.options
            ],
            "time_remaining_seconds": result.time_remaining_seconds,
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


def get_submit_answer_use_case(
    db: AsyncSession = Depends(get_db),
) -> SubmitAnswerUseCase:
    """Dependency to get SubmitAnswerUseCase."""
    trivia_repo = SQLAlchemyTriviaRepository(db)
    participation_repo = SQLAlchemyParticipationRepository(db)
    trivia_question_repo = SQLAlchemyTriviaQuestionRepository(db)
    question_repo = SQLAlchemyQuestionRepository(db)
    option_repo = SQLAlchemyOptionRepository(db)
    answer_repo = SQLAlchemyAnswerRepository(db)
    return SubmitAnswerUseCase(
        trivia_repo,
        participation_repo,
        trivia_question_repo,
        question_repo,
        option_repo,
        answer_repo,
    )


@router.post("/{trivia_id}/answer")
async def submit_answer(
    trivia_id: UUID,
    request: SubmitAnswerRequest,
    use_case: SubmitAnswerUseCase = Depends(get_submit_answer_use_case),
):
    """
    Submit an answer to the current question of a trivia.

    Args:
        trivia_id: The trivia ID
        request: Submit answer request with user_id and selected_option_id
        use_case: Submit answer use case

    Returns:
        Submit answer result DTO with score and correctness
    """
    try:
        result = await use_case.execute(
            trivia_id, request.user_id, request.selected_option_id
        )
        return {
            "trivia_id": str(result.trivia_id),
            "question_id": str(result.question_id),
            "selected_option_id": str(result.selected_option_id),
            "is_correct": result.is_correct,
            "earned_points": result.earned_points,
            "total_score": result.total_score,
            "time_remaining_seconds": result.time_remaining_seconds,
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
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


def get_advance_question_use_case(
    db: AsyncSession = Depends(get_db),
) -> AdvanceQuestionUseCase:
    """Dependency to get AdvanceQuestionUseCase."""
    trivia_repo = SQLAlchemyTriviaRepository(db)
    trivia_question_repo = SQLAlchemyTriviaQuestionRepository(db)
    return AdvanceQuestionUseCase(
        trivia_repo,
        trivia_question_repo,
    )


@router.post("/{trivia_id}/next-question")
async def advance_question(
    trivia_id: UUID,
    request: AdvanceQuestionRequest,
    use_case: AdvanceQuestionUseCase = Depends(get_advance_question_use_case),
):
    """
    Advance to the next question or finish the trivia.

    Args:
        trivia_id: The trivia ID
        request: Advance question request with admin_user_id
        use_case: Advance question use case

    Returns:
        Advance question result DTO with updated trivia state
    """
    try:
        result = await use_case.execute(trivia_id, request.admin_user_id)
        return {
            "trivia_id": str(result.trivia_id),
            "status": result.status.value,
            "current_question_index": result.current_question_index,
            "total_questions": result.total_questions,
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except InvalidStateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


def get_get_trivia_ranking_use_case(
    db: AsyncSession = Depends(get_db),
) -> GetTriviaRankingUseCase:
    """Dependency to get GetTriviaRankingUseCase."""
    trivia_repo = SQLAlchemyTriviaRepository(db)
    participation_repo = SQLAlchemyParticipationRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    return GetTriviaRankingUseCase(
        trivia_repo,
        participation_repo,
        user_repo,
    )


@router.get("/{trivia_id}/ranking")
async def get_trivia_ranking(
    trivia_id: UUID,
    use_case: GetTriviaRankingUseCase = Depends(get_get_trivia_ranking_use_case),
):
    """
    Get the current ranking of a trivia.

    Args:
        trivia_id: The trivia ID
        use_case: Get trivia ranking use case

    Returns:
        Trivia ranking DTO with participants ordered by score DESC
    """
    try:
        result = await use_case.execute(trivia_id)
        return {
            "trivia_id": str(result.trivia_id),
            "status": result.status.value,
            "ranking": [
                {
                    "position": entry.position,
                    "user_id": str(entry.user_id),
                    "user_name": entry.user_name,
                    "score": entry.score,
                }
                for entry in result.ranking
            ],
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

