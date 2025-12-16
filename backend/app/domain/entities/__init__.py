"""Domain entities."""
from app.domain.entities.user import User
from app.domain.entities.trivia import Trivia, TriviaStatus
from app.domain.entities.question import Question, QuestionDifficulty
from app.domain.entities.option import Option
from app.domain.entities.trivia_question import TriviaQuestion
from app.domain.entities.participation import Participation, ParticipationStatus
from app.domain.entities.answer import Answer

__all__ = [
    "User",
    "Trivia",
    "TriviaStatus",
    "Question",
    "QuestionDifficulty",
    "Option",
    "TriviaQuestion",
    "Participation",
    "ParticipationStatus",
    "Answer",
]

