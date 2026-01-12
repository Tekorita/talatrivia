"""API routers."""
from app.infrastructure.api.routers import (
    admin,
    auth,
    events,
    gameplay,
    health,
    lobby,
    play,
    questions,
    trivias,
    users,
)

__all__ = ["admin", "auth", "events", "gameplay", "health", "lobby", "play", "questions", "trivias", "users"]

