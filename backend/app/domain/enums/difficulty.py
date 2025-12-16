"""Difficulty enumeration."""
from enum import Enum


class Difficulty(str, Enum):
    """Question difficulty enumeration."""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"

