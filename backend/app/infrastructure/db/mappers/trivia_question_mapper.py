"""TriviaQuestion mapper."""
from app.domain.entities.trivia_question import TriviaQuestion
from app.infrastructure.db.models.trivia_question import TriviaQuestionModel


def to_domain(orm_model: TriviaQuestionModel) -> TriviaQuestion:
    """Convert TriviaQuestionModel to TriviaQuestion domain entity."""
    return TriviaQuestion(
        id=orm_model.id,
        trivia_id=orm_model.trivia_id,
        question_id=orm_model.question_id,
        position=orm_model.position,
        time_limit_seconds=orm_model.time_limit_seconds,
    )

