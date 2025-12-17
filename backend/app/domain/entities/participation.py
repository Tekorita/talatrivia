"""Participation domain entity."""
from datetime import datetime
from enum import Enum
from uuid import UUID


class ParticipationStatus(str, Enum):
    """Participation status enumeration."""
    INVITED = "INVITED"
    JOINED = "JOINED"
    READY = "READY"
    FINISHED = "FINISHED"
    DISCONNECTED = "DISCONNECTED"


class Participation:
    """Participation domain entity."""
    
    def __init__(
        self,
        id: UUID,
        trivia_id: UUID,
        user_id: UUID,
        status: ParticipationStatus = ParticipationStatus.INVITED,
        score: int = 0,
        joined_at: datetime | None = None,
        ready_at: datetime | None = None,
        finished_at: datetime | None = None,
    ):
        self.id = id
        self.trivia_id = trivia_id
        self.user_id = user_id
        self.status = status
        self.score = score
        self.joined_at = joined_at
        self.ready_at = ready_at
        self.finished_at = finished_at

