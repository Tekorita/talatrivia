"""Question domain entity."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from enum import Enum


class QuestionDifficulty(str, Enum):
    """Question difficulty enumeration."""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class Question:
    """Question domain entity."""
    
    def __init__(
        self,
        id: UUID,
        text: str,
        difficulty: QuestionDifficulty,
        created_by_user_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.text = text
        self.difficulty = difficulty
        self.created_by_user_id = created_by_user_id
        self.created_at = created_at or datetime.now(timezone.utc)

