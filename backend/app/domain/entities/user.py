"""User domain entity."""
from datetime import UTC, datetime
from uuid import UUID


class UserRole:
    """User roles."""
    ADMIN = "ADMIN"
    PLAYER = "PLAYER"


class User:
    """User domain entity."""
    
    def __init__(
        self,
        id: UUID,
        name: str,
        email: str,
        password_hash: str,
        role: str = UserRole.PLAYER,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at or datetime.now(UTC)

