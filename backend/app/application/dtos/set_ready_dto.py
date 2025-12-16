"""Set ready DTO."""
from dataclasses import dataclass
from uuid import UUID
from app.domain.enums.participation_status import ParticipationStatus


@dataclass
class SetReadyDTO:
    """DTO for set ready response."""
    participation_id: UUID
    participation_status: ParticipationStatus

