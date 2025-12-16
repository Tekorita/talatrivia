"""Participation mapper."""
from app.domain.entities.participation import Participation, ParticipationStatus
from app.infrastructure.db.models.participation import ParticipationModel


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
    )

