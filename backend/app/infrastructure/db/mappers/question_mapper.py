"""Question mapper."""
from datetime import UTC, datetime

from app.domain.entities.question import Question, QuestionDifficulty
from app.infrastructure.db.models.question import QuestionModel


def _to_naive_dt(dt: datetime | None) -> datetime | None:
    """Convert timezone-aware datetime to naive datetime."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # Convert to UTC and remove timezone info
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def to_domain(orm_model: QuestionModel) -> Question:
    """Convert QuestionModel to Question domain entity."""
    return Question(
        id=orm_model.id,
        text=orm_model.text,
        difficulty=QuestionDifficulty(orm_model.difficulty),
        created_by_user_id=orm_model.created_by_user_id,
        created_at=orm_model.created_at,
    )


def to_orm(question: Question) -> QuestionModel:
    """Convert Question domain entity to QuestionModel."""
    return QuestionModel(
        id=question.id,
        text=question.text,
        difficulty=question.difficulty.value,
        created_by_user_id=question.created_by_user_id,
        created_at=_to_naive_dt(question.created_at),
    )

