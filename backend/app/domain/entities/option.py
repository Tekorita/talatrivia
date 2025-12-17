"""Option domain entity."""
from datetime import UTC, datetime
from uuid import UUID


class Option:
    """Option domain entity."""
    
    def __init__(
        self,
        id: UUID,
        question_id: UUID,
        text: str,
        is_correct: bool,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.question_id = question_id
        self.text = text
        self.is_correct = is_correct
        self.created_at = created_at or datetime.now(UTC)

