"""User SQLAlchemy model."""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.infrastructure.db.base import Base


class UserRole:
    """User roles."""
    ADMIN = "ADMIN"
    PLAYER = "PLAYER"


class UserModel(Base):
    """User database model."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum("ADMIN", "PLAYER", name="user_role"), default=UserRole.PLAYER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

