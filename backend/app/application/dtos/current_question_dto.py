"""Current question DTO."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class OptionDTO:
    """Option DTO (without correct answer)."""
    option_id: UUID
    option_text: str


@dataclass
class CurrentQuestionDTO:
    """DTO for current question response."""
    question_id: UUID
    question_text: str
    options: list[OptionDTO]
    time_remaining_seconds: int
    fifty_fifty_available: bool

