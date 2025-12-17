"""Question domain entity."""
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID


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
        created_by_user_id: UUID | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.text = text
        self.difficulty = difficulty
        self.created_by_user_id = created_by_user_id
        self.created_at = created_at or datetime.now(UTC)

