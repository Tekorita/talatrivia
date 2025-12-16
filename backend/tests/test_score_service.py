"""Tests for ScoreService."""
from app.domain.enums.difficulty import Difficulty
from app.domain.services.score_service import ScoreService


def test_points_for_easy():
    """Test points calculation for EASY difficulty."""
    assert ScoreService.points_for(Difficulty.EASY) == 1


def test_points_for_medium():
    """Test points calculation for MEDIUM difficulty."""
    assert ScoreService.points_for(Difficulty.MEDIUM) == 2


def test_points_for_hard():
    """Test points calculation for HARD difficulty."""
    assert ScoreService.points_for(Difficulty.HARD) == 3

