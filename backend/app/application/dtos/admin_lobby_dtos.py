"""Lobby DTOs."""
from typing import List

from pydantic import BaseModel


class LobbyPlayerDTO(BaseModel):
    """Lobby player DTO."""
    user_id: str
    name: str
    present: bool
    ready: bool


class LobbyDTO(BaseModel):
    """Lobby DTO."""
    players: List[LobbyPlayerDTO]


# Keep AdminLobbyDTO for backward compatibility
class AdminLobbyPlayerDTO(LobbyPlayerDTO):
    """Admin lobby player DTO (deprecated, use LobbyPlayerDTO)."""
    pass


class AdminLobbyDTO(BaseModel):
    """Admin lobby DTO (includes counts)."""
    assigned_count: int
    present_count: int
    ready_count: int
    players: List[LobbyPlayerDTO]
