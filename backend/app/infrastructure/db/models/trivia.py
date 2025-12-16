"""Trivia SQLAlchemy model."""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.infrastructure.db.base import Base


class TriviaModel(Base):
    """Trivia database model."""
    __tablename__ = "trivias"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    topic = Column(String, nullable=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(
        SQLEnum("DRAFT", "LOBBY", "IN_PROGRESS", "FINISHED", name="trivia_status"),
        default="DRAFT",
        nullable=False
    )
    current_question_index = Column(Integer, default=0, nullable=False)
    question_started_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    
    # Relationships
    creator = relationship("UserModel", foreign_keys=[created_by_user_id])
    trivia_questions = relationship("TriviaQuestionModel", back_populates="trivia", cascade="all, delete-orphan")
    participations = relationship("ParticipationModel", back_populates="trivia", cascade="all, delete-orphan")

