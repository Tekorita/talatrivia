"""TriviaQuestion SQLAlchemy model."""
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.infrastructure.db.base import Base


class TriviaQuestionModel(Base):
    """TriviaQuestion database model (bridge table)."""
    __tablename__ = "trivia_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trivia_id = Column(UUID(as_uuid=True), ForeignKey("trivias.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    position = Column(Integer, nullable=False)
    time_limit_seconds = Column(Integer, nullable=False)
    
    # Relationships
    trivia = relationship("TriviaModel", back_populates="trivia_questions")
    question = relationship("QuestionModel", back_populates="trivia_questions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("trivia_id", "position", name="uq_trivia_position"),
        UniqueConstraint("trivia_id", "question_id", name="uq_trivia_question"),
    )

