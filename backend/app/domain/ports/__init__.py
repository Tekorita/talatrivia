"""Domain ports (interfaces)."""
from app.domain.ports.answer_repository import AnswerRepositoryPort
from app.domain.ports.option_repository import OptionRepositoryPort
from app.domain.ports.participation_repository import ParticipationRepositoryPort
from app.domain.ports.question_repository import QuestionRepositoryPort
from app.domain.ports.trivia_question_repository import TriviaQuestionRepositoryPort
from app.domain.ports.trivia_repository import TriviaRepositoryPort
from app.domain.ports.user_repository import UserRepositoryPort

__all__ = [
    "AnswerRepositoryPort",
    "OptionRepositoryPort",
    "ParticipationRepositoryPort",
    "QuestionRepositoryPort",
    "TriviaQuestionRepositoryPort",
    "TriviaRepositoryPort",
    "UserRepositoryPort",
]

