"""Fifty-fifty lifeline DTO."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class OptionDTO:
    """Option DTO (without correct answer)."""
    id: UUID
    text: str


@dataclass
class UseFiftyFiftyResultDTO:
    """DTO for use fifty-fifty lifeline result."""
    allowed_options: list[OptionDTO]
    fifty_fifty_used: bool

