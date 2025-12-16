"""Answer SQLAlchemy model."""
from sqlalchemy import Column, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.infrastructure.db.base import Base


class AnswerModel(Base):
    """Answer database model."""
    __tablename__ = "answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participation_id = Column(UUID(as_uuid=True), ForeignKey("participations.id"), nullable=False)
    trivia_question_id = Column(UUID(as_uuid=True), ForeignKey("trivia_questions.id"), nullable=False)
    selected_option_id = Column(UUID(as_uuid=True), ForeignKey("options.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    earned_points = Column(Integer, nullable=False)
    answered_at = Column(DateTime, nullable=False)
    
    # Relationships
    participation = relationship("ParticipationModel", back_populates="answers")
    trivia_question = relationship("TriviaQuestionModel")
    selected_option = relationship("OptionModel", foreign_keys=[selected_option_id])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("participation_id", "trivia_question_id", name="uq_participation_trivia_question"),
    )

