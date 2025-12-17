"""Option mapper."""
from app.domain.entities.option import Option
from app.infrastructure.db.models.option import OptionModel


def to_domain(orm_model: OptionModel) -> Option:
    """Convert OptionModel to Option domain entity."""
    return Option(
        id=orm_model.id,
        question_id=orm_model.question_id,
        text=orm_model.text,
        is_correct=orm_model.is_correct,
        created_at=orm_model.created_at,
    )

