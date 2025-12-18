"""Tests for play router - player lobby endpoint."""
from uuid import uuid4

from fastapi.testclient import TestClient

from app.domain.errors import NotFoundError
from app.infrastructure.api.routers.play import get_update_heartbeat_use_case
from app.main import app

client = TestClient(app)


def test_get_player_lobby_endpoint_not_found():
    """Test get player lobby endpoint with non-existent trivia."""
    trivia_id = uuid4()
    response = client.get(f"/play/trivias/{trivia_id}/lobby")
    assert response.status_code == 404


def test_get_player_lobby_endpoint_invalid_uuid():
    """Test get player lobby endpoint with invalid UUID."""
    response = client.get("/play/trivias/invalid-uuid/lobby")
    assert response.status_code == 422


def test_update_heartbeat_endpoint_not_found():
    """Test update heartbeat endpoint with non-existent trivia."""
    trivia_id = uuid4()
    user_id = uuid4()
    
    # Mock the use case to raise NotFoundError
    class MockUpdateHeartbeatUseCase:
        async def execute(self, trivia_id, user_id):
            raise NotFoundError(f"Trivia {trivia_id} not found")
    
    # Override the dependency
    app.dependency_overrides[get_update_heartbeat_use_case] = lambda: MockUpdateHeartbeatUseCase()
    
    try:
        response = client.post(
            f"/play/trivias/{trivia_id}/heartbeat",
            json={"user_id": str(user_id)}
        )
        assert response.status_code == 404
    finally:
        # Clean up the override
        app.dependency_overrides.clear()


def test_update_heartbeat_endpoint_invalid_uuid():
    """Test update heartbeat endpoint with invalid UUID."""
    response = client.post(
        "/play/trivias/invalid-uuid/heartbeat",
        json={"user_id": str(uuid4())}
    )
    assert response.status_code == 422


def test_update_heartbeat_endpoint_invalid_body():
    """Test update heartbeat endpoint with invalid body."""
    trivia_id = uuid4()
    response = client.post(f"/play/trivias/{trivia_id}/heartbeat", json={})
    assert response.status_code == 422
