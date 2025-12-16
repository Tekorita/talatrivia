"""ParticipationStatus enumeration."""
from enum import Enum


class ParticipationStatus(str, Enum):
    """Participation status enumeration."""
    INVITED = "INVITED"
    JOINED = "JOINED"
    READY = "READY"
    FINISHED = "FINISHED"
    DISCONNECTED = "DISCONNECTED"

