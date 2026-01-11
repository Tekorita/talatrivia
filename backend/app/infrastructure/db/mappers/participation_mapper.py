"""Participation mapper."""
from datetime import UTC, datetime

from app.domain.entities.participation import Participation, ParticipationStatus
from app.infrastructure.db.models.participation import ParticipationModel


def _to_naive_dt(dt: datetime | None) -> datetime | None:
    """Convert timezone-aware datetime to naive UTC datetime."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # Convert to UTC and remove timezone info
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def to_domain(orm_model: ParticipationModel) -> Participation:
    """Convert ParticipationModel to Participation domain entity."""
    return Participation(
        id=orm_model.id,
        trivia_id=orm_model.trivia_id,
        user_id=orm_model.user_id,
        status=ParticipationStatus(orm_model.status),
        score=orm_model.score,
        joined_at=orm_model.joined_at,
        ready_at=orm_model.ready_at,
        finished_at=orm_model.finished_at,
        last_seen_at=orm_model.last_seen_at,
        fifty_fifty_used=orm_model.fifty_fifty_used,
        fifty_fifty_question_id=orm_model.fifty_fifty_question_id,
    )

