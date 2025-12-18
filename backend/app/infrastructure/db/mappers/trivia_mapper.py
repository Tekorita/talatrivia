"""Trivia mapper."""
from datetime import UTC, datetime

from app.domain.entities.trivia import Trivia
from app.domain.enums.trivia_status import TriviaStatus
from app.infrastructure.db.models.trivia import TriviaModel


def _to_naive_dt(dt: datetime | None) -> datetime | None:
    """Convert timezone-aware datetime to naive datetime."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # Convert to UTC and remove timezone info
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def to_domain(orm_model: TriviaModel) -> Trivia:
    """Convert TriviaModel to Trivia domain entity."""
    return Trivia(
        id=orm_model.id,
        title=orm_model.title,
        description=orm_model.description,
        topic=orm_model.topic,
        created_by_user_id=orm_model.created_by_user_id,
        status=TriviaStatus(orm_model.status),
        current_question_index=orm_model.current_question_index,
        question_started_at=orm_model.question_started_at,
        created_at=orm_model.created_at,
        started_at=orm_model.started_at,
        finished_at=orm_model.finished_at,
    )


def to_orm(trivia: Trivia) -> TriviaModel:
    """Convert Trivia domain entity to TriviaModel."""
    return TriviaModel(
        id=trivia.id,
        title=trivia.title,
        description=trivia.description,
        topic=trivia.topic,
        created_by_user_id=trivia.created_by_user_id,
        status=trivia.status.value,
        current_question_index=trivia.current_question_index,
        question_started_at=_to_naive_dt(trivia.question_started_at),
        created_at=_to_naive_dt(trivia.created_at),
        started_at=_to_naive_dt(trivia.started_at),
        finished_at=_to_naive_dt(trivia.finished_at),
    )

