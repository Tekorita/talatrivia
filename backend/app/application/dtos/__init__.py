"""Application DTOs."""
from app.application.dtos.advance_question_dto import AdvanceQuestionResultDTO
from app.application.dtos.current_question_dto import CurrentQuestionDTO, OptionDTO
from app.application.dtos.join_trivia_dto import JoinTriviaDTO
from app.application.dtos.set_ready_dto import SetReadyDTO
from app.application.dtos.start_trivia_dto import StartTriviaDTO
from app.application.dtos.submit_answer_dto import SubmitAnswerResultDTO
from app.application.dtos.trivia_ranking_dto import RankingEntryDTO, TriviaRankingDTO

__all__ = [
    "AdvanceQuestionResultDTO",
    "CurrentQuestionDTO",
    "JoinTriviaDTO",
    "OptionDTO",
    "RankingEntryDTO",
    "SetReadyDTO",
    "StartTriviaDTO",
    "SubmitAnswerResultDTO",
    "TriviaRankingDTO",
]

