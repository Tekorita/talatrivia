"""Helper functions to emit SSE events from use cases."""
import logging
from uuid import UUID

from app.application.dtos.admin_lobby_dtos import AdminLobbyDTO, LobbyDTO
from app.application.dtos.current_question_dto import CurrentQuestionDTO
from app.application.dtos.trivia_ranking_dto import TriviaRankingDTO
from app.infrastructure.sse.sse_manager import get_sse_manager

logger = logging.getLogger(__name__)


def _to_dict_lobby_dto(dto: LobbyDTO) -> dict:
    """Convert LobbyDTO to dict for JSON serialization."""
    return {
        "players": [
            {
                "user_id": str(p.user_id),
                "name": p.name,
                "present": p.present,
                "ready": p.ready,
            }
            for p in dto.players
        ]
    }


def _to_dict_admin_lobby_dto(dto: AdminLobbyDTO) -> dict:
    """Convert AdminLobbyDTO to dict for JSON serialization."""
    return {
        "assigned_count": dto.assigned_count,
        "present_count": dto.present_count,
        "ready_count": dto.ready_count,
        "players": [
            {
                "user_id": str(p.user_id),
                "name": p.name,
                "present": p.present,
                "ready": p.ready,
            }
            for p in dto.players
        ],
    }


def _to_dict_current_question_dto(dto: CurrentQuestionDTO) -> dict:
    """Convert CurrentQuestionDTO to dict for JSON serialization.
    
    Note: fifty_fifty_available is NOT included in SSE events because it's
    player-specific. Each client should fetch their own current question
    to get their personal fifty_fifty_available status.
    """
    return {
        "question_id": str(dto.question_id),
        "question_text": dto.question_text,
        "options": [
            {
                "option_id": str(opt.option_id),
                "option_text": opt.option_text,
            }
            for opt in dto.options
        ],
        "time_remaining_seconds": dto.time_remaining_seconds,
        # fifty_fifty_available is NOT included - it's player-specific
        "question_index": dto.question_index,
        "total_questions": dto.total_questions,
    }


def _to_dict_trivia_ranking_dto(dto: TriviaRankingDTO) -> dict:
    """Convert TriviaRankingDTO to dict for JSON serialization."""
    return {
        "trivia_id": str(dto.trivia_id),
        "status": dto.status.value,
        "ranking": [
            {
                "position": entry.position,
                "user_id": str(entry.user_id),
                "user_name": entry.user_name,
                "score": entry.score,
            }
            for entry in dto.ranking
        ],
    }


def _to_dict_status_dto(trivia_id: UUID, status: str, current_question_index: int) -> dict:
    """Convert trivia status to dict for JSON serialization."""
    # Map backend status to frontend state
    state_map = {
        "DRAFT": "WAITING",
        "LOBBY": "WAITING",
        "IN_PROGRESS": "IN_PROGRESS",
        "FINISHED": "FINISHED",
    }
    state = state_map.get(status, "WAITING")
    
    return {
        "state": state,
        "current_question_index": current_question_index,
    }


async def emit_lobby_updated(trivia_id: UUID, lobby_dto: LobbyDTO) -> None:
    """Emit lobby_updated event."""
    sse_manager = get_sse_manager()
    data = _to_dict_lobby_dto(lobby_dto)
    await sse_manager.broadcast(trivia_id, "lobby_updated", data)
    logger.info(f"Emitted lobby_updated event for trivia {trivia_id}")


async def emit_admin_lobby_updated(trivia_id: UUID, admin_lobby_dto: AdminLobbyDTO) -> None:
    """Emit admin_lobby_updated event."""
    sse_manager = get_sse_manager()
    data = _to_dict_admin_lobby_dto(admin_lobby_dto)
    await sse_manager.broadcast(trivia_id, "admin_lobby_updated", data)
    logger.info(f"Emitted admin_lobby_updated event for trivia {trivia_id}")


async def emit_status_updated(
    trivia_id: UUID, status: str, current_question_index: int
) -> None:
    """Emit status_updated event."""
    sse_manager = get_sse_manager()
    data = _to_dict_status_dto(trivia_id, status, current_question_index)
    await sse_manager.broadcast(trivia_id, "status_updated", data)
    logger.info(f"Emitted status_updated event for trivia {trivia_id}")


async def emit_current_question_updated(
    trivia_id: UUID, question_dto: CurrentQuestionDTO
) -> None:
    """Emit current_question_updated event."""
    sse_manager = get_sse_manager()
    data = _to_dict_current_question_dto(question_dto)
    await sse_manager.broadcast(trivia_id, "current_question_updated", data)
    logger.info(f"Emitted current_question_updated event for trivia {trivia_id}")


async def emit_ranking_updated(trivia_id: UUID, ranking_dto: TriviaRankingDTO) -> None:
    """Emit ranking_updated event."""
    sse_manager = get_sse_manager()
    data = _to_dict_trivia_ranking_dto(ranking_dto)
    await sse_manager.broadcast(trivia_id, "ranking_updated", data)
    logger.info(f"Emitted ranking_updated event for trivia {trivia_id}")

