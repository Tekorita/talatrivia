"""SQLAlchemy models."""
from app.infrastructure.db.models.answer import AnswerModel
from app.infrastructure.db.models.option import OptionModel
from app.infrastructure.db.models.participation import ParticipationModel
from app.infrastructure.db.models.question import QuestionModel
from app.infrastructure.db.models.trivia import TriviaModel
from app.infrastructure.db.models.trivia_question import TriviaQuestionModel
from app.infrastructure.db.models.user import UserModel

__all__ = [
    "UserModel",
    "TriviaModel",
    "QuestionModel",
    "OptionModel",
    "TriviaQuestionModel",
    "ParticipationModel",
    "AnswerModel",
]

