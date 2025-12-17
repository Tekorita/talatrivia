"""Trivia ranking DTOs."""
from dataclasses import dataclass
from typing import List
from uuid import UUID

from app.domain.enums.trivia_status import TriviaStatus


@dataclass
class RankingEntryDTO:
    """Ranking entry DTO."""
    position: int
    user_id: UUID
    user_name: str
    score: int


@dataclass
class TriviaRankingDTO:
    """Trivia ranking DTO."""
    trivia_id: UUID
    status: TriviaStatus
    ranking: List[RankingEntryDTO]

