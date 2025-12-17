"""Start trivia DTO."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums.trivia_status import TriviaStatus


@dataclass
class StartTriviaDTO:
    """DTO for start trivia response."""
    trivia_id: UUID
    trivia_status: TriviaStatus
    started_at: datetime
    current_question_index: int

