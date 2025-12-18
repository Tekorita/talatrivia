"""Questions router."""
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.question import Question, QuestionDifficulty
from app.infrastructure.db.models.option import OptionModel
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.repositories import SQLAlchemyQuestionRepository
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/questions", tags=["questions"])


class OptionRequest(BaseModel):
    """Option request."""
    text: str
    is_correct: bool


class CreateQuestionRequest(BaseModel):
    """Create question request."""
    text: str
    difficulty: str  # EASY, MEDIUM, HARD
    options: list[OptionRequest]


class QuestionResponse(BaseModel):
    """Question response."""
    id: str
    text: str
    difficulty: str
    created_by_user_id: str | None = None


@router.get("", response_model=list[QuestionResponse])
async def list_questions(
    db: AsyncSession = Depends(get_db),
):
    """
    List all questions.
    
    Args:
        db: Database session
        
    Returns:
        List of questions
    """
    question_repo = SQLAlchemyQuestionRepository(db)
    questions = await question_repo.list_all()
    return [
        QuestionResponse(
            id=str(question.id),
            text=question.text,
            difficulty=question.difficulty.value,
            created_by_user_id=str(question.created_by_user_id) if question.created_by_user_id else None,
        )
        for question in questions
    ]


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    request: CreateQuestionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new question with options.
    
    Args:
        request: Create question request
        db: Database session
        
    Returns:
        Created question
        
    Raises:
        HTTPException: 422 if validation fails, 500 if server error
    """
    try:
        # Validate difficulty
        try:
            difficulty = QuestionDifficulty(request.difficulty.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid difficulty: {request.difficulty}. Must be EASY, MEDIUM, or HARD",
            )
        
        # Validate options
        if len(request.options) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least 2 options are required",
            )
        
        correct_count = sum(1 for opt in request.options if opt.is_correct)
        if correct_count != 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Exactly one option must be marked as correct",
            )
        
        # Get first admin user as creator (temporary solution)
        result = await db.execute(
            select(UserModel).where(UserModel.role == "ADMIN").limit(1)
        )
        admin_user = result.scalar_one_or_none()
        
        created_by_user_id = admin_user.id if admin_user else None
        
        # Create question entity
        new_question = Question(
            id=uuid4(),
            text=request.text,
            difficulty=difficulty,
            created_by_user_id=created_by_user_id,
        )
        
        # Save question
        question_repo = SQLAlchemyQuestionRepository(db)
        created_question = await question_repo.create(new_question)
        
        # Create options
        for option_req in request.options:
            option = OptionModel(
                id=uuid4(),
                question_id=created_question.id,
                text=option_req.text,
                is_correct=option_req.is_correct,
            )
            db.add(option)
        
        await db.commit()
        
        return QuestionResponse(
            id=str(created_question.id),
            text=created_question.text,
            difficulty=created_question.difficulty.value,
            created_by_user_id=str(created_question.created_by_user_id) if created_question.created_by_user_id else None,
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Rollback on any other error
        await db.rollback()
        # Log the error for debugging
        import traceback
        error_detail = f"Internal server error: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        ) from e
