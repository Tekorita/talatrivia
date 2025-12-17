"""Trivia domain entity."""
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID


class TriviaStatus(str, Enum):
    """Trivia status enumeration."""
    DRAFT = "DRAFT"
    LOBBY = "LOBBY"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"


class Trivia:
    """Trivia domain entity."""
    
    def __init__(
        self,
        id: UUID,
        title: str,
        description: str,
        created_by_user_id: UUID,
        topic: str | None = None,
        status: TriviaStatus = TriviaStatus.DRAFT,
        current_question_index: int = 0,
        question_started_at: datetime | None = None,
        created_at: datetime | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ):
        self.id = id
        self.title = title
        self.description = description
        self.topic = topic
        self.created_by_user_id = created_by_user_id
        self.status = status
        self.current_question_index = current_question_index
        self.question_started_at = question_started_at
        self.created_at = created_at or datetime.now(UTC)
        self.started_at = started_at
        self.finished_at = finished_at

