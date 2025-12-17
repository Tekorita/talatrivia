"""Advance question DTO."""
from dataclasses import dataclass
from uuid import UUID

from app.domain.enums.trivia_status import TriviaStatus


@dataclass
class AdvanceQuestionResultDTO:
    """DTO for advance question result."""
    trivia_id: UUID
    status: TriviaStatus
    current_question_index: int
    total_questions: int

