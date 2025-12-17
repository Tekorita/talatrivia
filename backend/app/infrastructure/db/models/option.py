"""Option SQLAlchemy model."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.db.base import Base


class OptionModel(Base):
    """Option database model."""
    __tablename__ = "options"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    text = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    question = relationship("QuestionModel", back_populates="options")
    
    # Constraints
    # Partial unique index: only one correct option per question
    # Note: This constraint will be enforced at the application level
    # For database-level enforcement, we'll add it via a migration
    __table_args__ = ()

