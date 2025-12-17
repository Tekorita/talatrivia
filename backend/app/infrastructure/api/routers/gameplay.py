"""Gameplay router."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories import (
    SQLAlchemyAnswerRepository,
    SQLAlchemyOptionRepository,
    SQLAlchemyParticipationRepository,
    SQLAlchemyQuestionRepository,
    SQLAlchemyTriviaQuestionRepository,
    SQLAlchemyTriviaRepository,
)
from app.application.use_cases.get_current_question import GetCurrentQuestionUseCase
from app.application.use_cases.submit_answer import SubmitAnswerUseCase
from app.domain.errors import ConflictError, InvalidStateError, NotFoundError

router = APIRouter(prefix="/trivias", tags=["gameplay"])


class SubmitAnswerRequest(BaseModel):
    """Submit answer request."""
    user_id: UUID
    selected_option_id: UUID


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

