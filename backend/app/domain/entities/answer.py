"""Answer domain entity."""
from datetime import datetime
from uuid import UUID


class Answer:
    """Answer domain entity."""
    
    def __init__(
        self,
        id: UUID,
        participation_id: UUID,
        trivia_question_id: UUID,
        selected_option_id: UUID,
        is_correct: bool,
        earned_points: int,
        answered_at: datetime,
    ):
        self.id = id
        self.participation_id = participation_id
        self.trivia_question_id = trivia_question_id
        self.selected_option_id = selected_option_id
        self.is_correct = is_correct
        self.earned_points = earned_points
        self.answered_at = answered_at

