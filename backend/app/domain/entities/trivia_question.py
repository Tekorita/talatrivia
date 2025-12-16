"""TriviaQuestion domain entity."""
from uuid import UUID


class TriviaQuestion:
    """TriviaQuestion domain entity (bridge table)."""
    
    def __init__(
        self,
        id: UUID,
        trivia_id: UUID,
        question_id: UUID,
        position: int,
        time_limit_seconds: int,
    ):
        self.id = id
        self.trivia_id = trivia_id
        self.question_id = question_id
        self.position = position
        self.time_limit_seconds = time_limit_seconds

