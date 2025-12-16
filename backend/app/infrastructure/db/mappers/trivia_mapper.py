"""Trivia mapper."""
from app.domain.entities.trivia import Trivia
from app.domain.enums.trivia_status import TriviaStatus
from app.infrastructure.db.models.trivia import TriviaModel


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

