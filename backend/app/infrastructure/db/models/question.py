"""Question SQLAlchemy model."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.db.base import Base


class QuestionModel(Base):
    """Question database model."""
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(String, nullable=False)
    difficulty = Column(
        SQLEnum("EASY", "MEDIUM", "HARD", name="question_difficulty"),
        nullable=False
    )
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    creator = relationship("UserModel", foreign_keys=[created_by_user_id])
    options = relationship("OptionModel", back_populates="question", cascade="all, delete-orphan")
    trivia_questions = relationship("TriviaQuestionModel", back_populates="question")

