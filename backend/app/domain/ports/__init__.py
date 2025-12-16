"""Domain ports (interfaces)."""
from app.domain.ports.trivia_repository import TriviaRepositoryPort
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.user_repository import UserRepositoryPort

__all__ = [
    "TriviaRepositoryPort",
    "ParticipationRepositoryPort",
    "UserRepositoryPort",
]

