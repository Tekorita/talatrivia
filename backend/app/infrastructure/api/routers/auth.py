"""Auth router."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.password import verify_password
from app.infrastructure.db.repositories import SQLAlchemyUserRepository
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response."""
    id: str
    name: str
    email: str
    role: str


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user with email and password.
    
    Args:
        request: Login request with email and password
        db: Database session
        
    Returns:
        User information (id, name, email, role)
        
    Raises:
        HTTPException: 401 if invalid credentials, 404 if user not found
    """
    user_repo = SQLAlchemyUserRepository(db)
    user = await user_repo.get_by_email(request.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    return LoginResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
    )
