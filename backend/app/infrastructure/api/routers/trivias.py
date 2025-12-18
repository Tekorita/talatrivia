"""Trivias router."""
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.participation import ParticipationStatus
from app.domain.entities.trivia import Trivia, TriviaStatus
from app.infrastructure.db.models.answer import AnswerModel
from app.infrastructure.db.models.participation import ParticipationModel
from app.infrastructure.db.models.question import QuestionModel
from app.infrastructure.db.models.trivia_question import TriviaQuestionModel
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.repositories import (
    SQLAlchemyTriviaQuestionRepository,
    SQLAlchemyTriviaRepository,
    SQLAlchemyUserRepository,
)
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/trivias", tags=["trivias"])


class CreateTriviaRequest(BaseModel):
    """Create trivia request."""
    title: str
    description: str
    user_ids: list[str] = []  # Players to associate (will be converted to UUID)
    question_ids: list[str] = []  # Optional - questions to associate (will be converted to UUID)


class TriviaResponse(BaseModel):
    """Trivia response."""
    id: str
    title: str
    description: str
    created_by_user_id: str
    status: str
    current_question_index: int
    created_at: str | None = None


@router.get("", response_model=list[TriviaResponse])
async def list_trivias(
    db: AsyncSession = Depends(get_db),
):
    """
    List all trivias.
    
    Args:
        db: Database session
        
    Returns:
        List of trivias
    """
    trivia_repo = SQLAlchemyTriviaRepository(db)
    trivias = await trivia_repo.list_all()
    return [
        TriviaResponse(
            id=str(trivia.id),
            title=trivia.title,
            description=trivia.description,
            created_by_user_id=str(trivia.created_by_user_id),
            status=trivia.status.value,
            current_question_index=trivia.current_question_index,
            created_at=trivia.created_at.isoformat() if trivia.created_at else None,
        )
        for trivia in trivias
    ]


@router.get("/{trivia_id}", response_model=TriviaResponse)
async def get_trivia(
    trivia_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get trivia by ID.
    
    Args:
        trivia_id: The trivia ID
        db: Database session
        
    Returns:
        Trivia details
        
    Raises:
        HTTPException: 404 if trivia not found
    """
    trivia_repo = SQLAlchemyTriviaRepository(db)
    trivia = await trivia_repo.get_by_id(trivia_id)
    
    if not trivia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trivia {trivia_id} not found",
        )
    
    return TriviaResponse(
        id=str(trivia.id),
        title=trivia.title,
        description=trivia.description,
        created_by_user_id=str(trivia.created_by_user_id),
        status=trivia.status.value,
        current_question_index=trivia.current_question_index,
        created_at=trivia.created_at.isoformat() if trivia.created_at else None,
    )


@router.post("", response_model=TriviaResponse, status_code=status.HTTP_201_CREATED)
async def create_trivia(
    request: CreateTriviaRequest,
    db: AsyncSession = Depends(get_db),
    # TODO: Add authentication to get current user
    # For now, we'll use a default admin user ID
):
    """
    Create a new trivia.
    
    Args:
        request: Create trivia request
        db: Database session
        
    Returns:
        Created trivia
        
    Raises:
        HTTPException: 404 if user not found, 422 if validation fails, 500 if server error
    """
    try:
        # TODO: Get current user from authentication
        # For now, use a default admin user ID or get from request
        # We'll need to get the first admin user or require it in the request
        user_repo = SQLAlchemyUserRepository(db)
        
        # Get first admin user as creator (temporary solution)
        # In production, this should come from authentication
        result = await db.execute(
            select(UserModel).where(UserModel.role == "ADMIN").limit(1)
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No admin user found. Please create an admin user first.",
            )
        
        created_by_user_id = admin_user.id
        
        # Create trivia entity
        new_trivia = Trivia(
            id=uuid4(),
            title=request.title,
            description=request.description,
            created_by_user_id=created_by_user_id,
            status=TriviaStatus.DRAFT,
            current_question_index=0,
        )
        
        # Save trivia
        trivia_repo = SQLAlchemyTriviaRepository(db)
        created_trivia = await trivia_repo.create(new_trivia)
        
        # Associate users (create participations)
        if request.user_ids:
            for user_id_str in request.user_ids:
                # Convert string to UUID
                try:
                    user_id = UUID(user_id_str) if isinstance(user_id_str, str) else user_id_str
                except (ValueError, TypeError):
                    await db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid user_id format: {user_id_str}",
                    )
                
                # Verify user exists
                user = await user_repo.get_by_id(user_id)
                if not user:
                    await db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"User {user_id} not found",
                    )
                
                # Create participation
                participation = ParticipationModel(
                    id=uuid4(),
                    trivia_id=created_trivia.id,
                    user_id=user_id,
                    status=ParticipationStatus.INVITED.value,
                    score=0,
                )
                db.add(participation)
        
        # Associate questions (create trivia_questions) - optional
        if request.question_ids:
            trivia_question_repo = SQLAlchemyTriviaQuestionRepository(db)
            current_count = await trivia_question_repo.count_by_trivia(created_trivia.id)
            
            for question_id_str in request.question_ids:
                # Convert string to UUID
                try:
                    question_id = UUID(question_id_str) if isinstance(question_id_str, str) else question_id_str
                except (ValueError, TypeError):
                    await db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid question_id format: {question_id_str}",
                    )
                
                # Verify question exists
                result = await db.execute(
                    select(QuestionModel).where(QuestionModel.id == question_id)
                )
                question = result.scalar_one_or_none()
                if not question:
                    await db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Question {question_id} not found",
                    )
                
                # Create trivia_question
                trivia_question = TriviaQuestionModel(
                    id=uuid4(),
                    trivia_id=created_trivia.id,
                    question_id=question_id,
                    position=current_count,
                    time_limit_seconds=30,  # Default time limit
                )
                db.add(trivia_question)
                current_count += 1
        
        await db.commit()
        
        return TriviaResponse(
            id=str(created_trivia.id),
            title=created_trivia.title,
            description=created_trivia.description,
            created_by_user_id=str(created_trivia.created_by_user_id),
            status=created_trivia.status.value,
            current_question_index=created_trivia.current_question_index,
            created_at=created_trivia.created_at.isoformat() if created_trivia.created_at else None,
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


@router.get("/{trivia_id}/questions", response_model=list[dict])
async def list_trivia_questions(
    trivia_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    List questions associated with a trivia.
    
    Args:
        trivia_id: The trivia ID
        db: Database session
        
    Returns:
        List of questions associated with the trivia
        
    Raises:
        HTTPException: 404 if trivia not found
    """
    trivia_repo = SQLAlchemyTriviaRepository(db)
    trivia = await trivia_repo.get_by_id(trivia_id)
    
    if not trivia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trivia {trivia_id} not found",
        )
    
    # Get trivia questions
    result = await db.execute(
        select(TriviaQuestionModel, QuestionModel)
        .join(QuestionModel, TriviaQuestionModel.question_id == QuestionModel.id)
        .where(TriviaQuestionModel.trivia_id == trivia_id)
        .order_by(TriviaQuestionModel.position)
    )
    
    questions = []
    for _trivia_question_model, question_model in result.all():
        questions.append({
            "id": str(question_model.id),
            "text": question_model.text,
            "difficulty": question_model.difficulty,
        })
    
    return questions


class AddQuestionToTriviaRequest(BaseModel):
    """Add question to trivia request."""
    question_id: str


@router.post("/{trivia_id}/questions", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_question_to_trivia(
    trivia_id: UUID,
    request: AddQuestionToTriviaRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a question to a trivia.
    
    Args:
        trivia_id: The trivia ID
        request: Request with question_id
        db: Database session
        
    Returns:
        Success response with question_id
        
    Raises:
        HTTPException: 404 if trivia or question not found, 422 if validation fails
    """
    try:
        # Get question_id from request
        question_id_str = request.question_id
        if not question_id_str:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="question_id is required",
            )
        
        # Convert string to UUID
        try:
            question_id = UUID(question_id_str) if isinstance(question_id_str, str) else question_id_str
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid question_id format: {question_id_str}",
            )
        
        # Verify trivia exists
        trivia_repo = SQLAlchemyTriviaRepository(db)
        trivia = await trivia_repo.get_by_id(trivia_id)
        if not trivia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trivia {trivia_id} not found",
            )
        
        # Verify question exists
        result = await db.execute(
            select(QuestionModel).where(QuestionModel.id == question_id)
        )
        question = result.scalar_one_or_none()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question {question_id} not found",
            )
        
        # Check if question is already associated
        existing = await db.execute(
            select(TriviaQuestionModel).where(
                TriviaQuestionModel.trivia_id == trivia_id,
                TriviaQuestionModel.question_id == question_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Question {question_id} is already associated with trivia {trivia_id}",
            )
        
        # Get current count for position
        trivia_question_repo = SQLAlchemyTriviaQuestionRepository(db)
        current_count = await trivia_question_repo.count_by_trivia(trivia_id)
        
        # Create trivia_question
        trivia_question = TriviaQuestionModel(
            id=uuid4(),
            trivia_id=trivia_id,
            question_id=question_id,
            position=current_count,
            time_limit_seconds=30,  # Default time limit
        )
        db.add(trivia_question)
        await db.commit()
        
        return {"question_id": str(question_id)}
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


class TriviaPlayerResponse(BaseModel):
    """User response for trivia players."""
    id: str
    name: str
    email: str
    role: str


@router.get("/{trivia_id}/players", response_model=list[TriviaPlayerResponse])
async def list_trivia_players(
    trivia_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    List players assigned to a trivia.
    
    Args:
        trivia_id: The trivia ID
        db: Database session
        
    Returns:
        List of users assigned to the trivia
        
    Raises:
        HTTPException: 404 if trivia not found
    """
    # Verify trivia exists
    trivia_repo = SQLAlchemyTriviaRepository(db)
    trivia = await trivia_repo.get_by_id(trivia_id)
    if not trivia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trivia {trivia_id} not found",
        )
    
    # Get participations for this trivia
    result = await db.execute(
        select(ParticipationModel, UserModel)
        .join(UserModel, ParticipationModel.user_id == UserModel.id)
        .where(ParticipationModel.trivia_id == trivia_id)
    )
    
    players = []
    for _participation_model, user_model in result.all():
        players.append({
            "id": str(user_model.id),
            "name": user_model.name,
            "email": user_model.email,
            "role": user_model.role,
        })
    
    return players


@router.post("/{trivia_id}/reset", response_model=dict)
async def reset_trivia(
    trivia_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset a trivia to LOBBY, clear answers and reset participation scores.
    """
    # Verify trivia exists
    trivia_repo = SQLAlchemyTriviaRepository(db)
    trivia = await trivia_repo.get_by_id(trivia_id)
    if not trivia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trivia {trivia_id} not found",
        )

    # Delete answers for participations of this trivia
    participation_ids_stmt = select(ParticipationModel.id).where(
        ParticipationModel.trivia_id == trivia_id
    )
    await db.execute(
        delete(AnswerModel).where(AnswerModel.participation_id.in_(participation_ids_stmt))
    )

    # Reset participation scores
    await db.execute(
        update(ParticipationModel)
        .where(ParticipationModel.trivia_id == trivia_id)
        .values(score=0)
    )

    # Reset trivia status and pointers
    trivia.status = TriviaStatus.LOBBY
    trivia.current_question_index = 0
    trivia.question_started_at = None
    trivia.started_at = None
    trivia.finished_at = None
    await trivia_repo.update(trivia)

    await db.commit()
    return {"status": "ok"}


class AddPlayerToTriviaRequest(BaseModel):
    """Add player to trivia request."""
    user_id: str


@router.post("/{trivia_id}/players", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_player_to_trivia(
    trivia_id: UUID,
    request: AddPlayerToTriviaRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a player to a trivia (create participation).
    
    Args:
        trivia_id: The trivia ID
        request: Request with user_id
        db: Database session
        
    Returns:
        Success response with user_id
        
    Raises:
        HTTPException: 404 if trivia or user not found, 409 if already assigned, 422 if validation fails
    """
    try:
        # Convert string to UUID
        try:
            user_id = UUID(request.user_id) if isinstance(request.user_id, str) else request.user_id
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid user_id format: {request.user_id}",
            )
        
        # Verify trivia exists
        trivia_repo = SQLAlchemyTriviaRepository(db)
        trivia = await trivia_repo.get_by_id(trivia_id)
        if not trivia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trivia {trivia_id} not found",
            )
        
        # Verify user exists
        user_repo = SQLAlchemyUserRepository(db)
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        
        # Check if participation already exists
        existing = await db.execute(
            select(ParticipationModel).where(
                ParticipationModel.trivia_id == trivia_id,
                ParticipationModel.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User {user_id} is already assigned to trivia {trivia_id}",
            )
        
        # Create participation
        participation = ParticipationModel(
            id=uuid4(),
            trivia_id=trivia_id,
            user_id=user_id,
            status=ParticipationStatus.INVITED.value,
            score=0,
        )
        db.add(participation)
        await db.commit()
        
        return {"user_id": str(user_id)}
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
