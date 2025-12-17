"""Question mapper."""
from app.domain.entities.question import Question, QuestionDifficulty
from app.infrastructure.db.models.question import QuestionModel


def to_domain(orm_model: QuestionModel) -> Question:
    """Convert QuestionModel to Question domain entity."""
    return Question(
        id=orm_model.id,
        text=orm_model.text,
        difficulty=QuestionDifficulty(orm_model.difficulty),
        created_by_user_id=orm_model.created_by_user_id,
        created_at=orm_model.created_at,
    )

