"""Participation SQLAlchemy model."""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.infrastructure.db.base import Base


class ParticipationModel(Base):
    """Participation database model."""
    __tablename__ = "participations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trivia_id = Column(UUID(as_uuid=True), ForeignKey("trivias.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(
        SQLEnum("INVITED", "JOINED", "READY", "FINISHED", "DISCONNECTED", name="participation_status"),
        default="INVITED",
        nullable=False
    )
    score = Column(Integer, default=0, nullable=False)
    joined_at = Column(DateTime, nullable=True)
    ready_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    
    # Relationships
    trivia = relationship("TriviaModel", back_populates="participations")
    user = relationship("UserModel", foreign_keys=[user_id])
    answers = relationship("AnswerModel", back_populates="participation", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("trivia_id", "user_id", name="uq_trivia_user"),
    )

