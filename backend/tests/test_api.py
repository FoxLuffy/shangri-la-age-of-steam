import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main
from main import app
from backend.models import NarrativeResult

def test_health_check():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_chat_endpoint():
    client = TestClient(app)
    payload = {"action_text": "Hello", "current_location_id": "1"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    assert "narration" in response.json()
