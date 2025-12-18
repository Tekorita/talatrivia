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


def to_orm(user: User) -> UserModel:
    """Convert User domain entity to UserModel."""
    return UserModel(
        id=user.id,
        name=user.name,
        email=user.email,
        password_hash=user.password_hash,
        role=user.role,
        created_at=user.created_at,
    )

