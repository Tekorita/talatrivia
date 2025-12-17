"""Answer mapper."""
from app.domain.entities.answer import Answer
from app.infrastructure.db.models.answer import AnswerModel


def to_domain(orm_model: AnswerModel) -> Answer:
    """Convert AnswerModel to Answer domain entity."""
    return Answer(
        id=orm_model.id,
        participation_id=orm_model.participation_id,
        trivia_question_id=orm_model.trivia_question_id,
        selected_option_id=orm_model.selected_option_id,
        is_correct=orm_model.is_correct,
        earned_points=orm_model.earned_points,
        answered_at=orm_model.answered_at,
    )

