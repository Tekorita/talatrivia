"""Join trivia DTO."""
from dataclasses import dataclass
from uuid import UUID
from app.domain.enums.trivia_status import TriviaStatus
from app.domain.enums.participation_status import ParticipationStatus


@dataclass
class JoinTriviaDTO:
    """DTO for join trivia response."""
    trivia_id: UUID
    participation_id: UUID
    participation_status: ParticipationStatus
    trivia_status: TriviaStatus

