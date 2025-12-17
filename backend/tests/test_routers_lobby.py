"""Tests for lobby router - basic endpoint coverage."""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_join_trivia_endpoint_invalid_body():
    """Test join trivia endpoint with invalid body."""
    trivia_id = uuid4()
    response = client.post(f"/trivias/{trivia_id}/join", json={})
    assert response.status_code == 422


def test_set_ready_endpoint_invalid_body():
    """Test set ready endpoint with invalid body."""
    trivia_id = uuid4()
    response = client.post(f"/trivias/{trivia_id}/ready", json={})
    assert response.status_code == 422


def test_start_trivia_endpoint_invalid_body():
    """Test start trivia endpoint with invalid body."""
    trivia_id = uuid4()
    response = client.post(f"/trivias/{trivia_id}/start", json={})
    assert response.status_code == 422


def test_join_trivia_endpoint_invalid_uuid():
    """Test join trivia endpoint with invalid UUID."""
    response = client.post("/trivias/invalid-uuid/join", json={"user_id": str(uuid4())})
    assert response.status_code == 422

