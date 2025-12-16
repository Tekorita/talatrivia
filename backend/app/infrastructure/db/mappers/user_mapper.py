"""User mapper."""
from app.domain.entities.user import User
from app.infrastructure.db.models.user import UserModel


def to_domain(orm_model: UserModel) -> User:
    """Convert UserModel to User domain entity."""
    return User(
        id=orm_model.id,
        name=orm_model.name,
        email=orm_model.email,
        password_hash=orm_model.password_hash,
        role=orm_model.role,
        created_at=orm_model.created_at,
    )

