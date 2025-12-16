"""TriviaStatus enumeration."""
from enum import Enum


class TriviaStatus(str, Enum):
    """Trivia status enumeration."""
    DRAFT = "DRAFT"
    LOBBY = "LOBBY"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"

