"""Submit answer DTO."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class SubmitAnswerResultDTO:
    """DTO for submit answer response."""
    trivia_id: UUID
    question_id: UUID
    selected_option_id: UUID
    is_correct: bool
    earned_points: int
    total_score: int
    time_remaining_seconds: int

