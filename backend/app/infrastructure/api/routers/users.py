"""Users router."""
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.password import hash_password
from app.domain.entities.user import User, UserRole
from app.infrastructure.db.repositories import SQLAlchemyUserRepository
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    """User response."""
    id: str
    name: str
    email: str
    role: str
    created_at: str | None = None


class CreateUserRequest(BaseModel):
    """Create user request."""
    name: str
    email: EmailStr
    password: str
    role: str = UserRole.PLAYER


@router.get("", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
):
    """
    List all users.
    
    Args:
        db: Database session
        
    Returns:
        List of users
    """
    user_repo = SQLAlchemyUserRepository(db)
    users = await user_repo.list_all()
    return [
        UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
            created_at=user.created_at.isoformat() if user.created_at else None,
        )
        for user in users
    ]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user.
    
    Args:
        request: Create user request
        db: Database session
        
    Returns:
        Created user
        
    Raises:
        HTTPException: 409 if email already exists
    """
    user_repo = SQLAlchemyUserRepository(db)
    
    # Check if user with email already exists
    existing_user = await user_repo.get_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )
    
    # Hash password
    password_hash = hash_password(request.password)
    
    # Create user entity
    new_user = User(
        id=uuid4(),
        name=request.name,
        email=request.email,
        password_hash=password_hash,
        role=request.role,
    )
    
    # Save to database
    created_user = await user_repo.create(new_user)
    await db.commit()
    
    return UserResponse(
        id=str(created_user.id),
        name=created_user.name,
        email=created_user.email,
        role=created_user.role,
        created_at=created_user.created_at.isoformat() if created_user.created_at else None,
    )
