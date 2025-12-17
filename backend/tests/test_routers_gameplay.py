"""Tests for gameplay router."""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


"""Tests for gameplay router - basic endpoint coverage."""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_current_question_endpoint_missing_user_id():
    """Test get current question endpoint without user_id parameter."""
    trivia_id = uuid4()
    # Missing user_id query parameter should return 422
    response = client.get(f"/trivias/{trivia_id}/current-question")
    assert response.status_code == 422


def test_get_trivia_ranking_endpoint_invalid_uuid():
    """Test get trivia ranking endpoint with invalid UUID."""
    response = client.get("/trivias/invalid-uuid/ranking")
    assert response.status_code == 422


def test_submit_answer_endpoint_invalid_body():
    """Test submit answer endpoint with invalid body."""
    trivia_id = uuid4()
    response = client.post(f"/trivias/{trivia_id}/answer", json={})
    assert response.status_code == 422


def test_advance_question_endpoint_invalid_body():
    """Test advance question endpoint with invalid body."""
    trivia_id = uuid4()
    response = client.post(f"/trivias/{trivia_id}/next-question", json={})
    assert response.status_code == 422

