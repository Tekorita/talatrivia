"""Score calculation service."""
from app.domain.enums.difficulty import Difficulty


class ScoreService:
    """Service for calculating points based on question difficulty."""
    
    @staticmethod
    def points_for(difficulty: Difficulty) -> int:
        """
        Calculate points for a given difficulty.
        
        Args:
            difficulty: The question difficulty
            
        Returns:
            Points awarded for the difficulty
        """
        mapping = {
            Difficulty.EASY: 1,
            Difficulty.MEDIUM: 2,
            Difficulty.HARD: 3,
        }
        return mapping.get(difficulty, 0)

