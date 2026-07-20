from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from backend.models import NarrativeResult

# Mocking the engine and clients
import main
main.engine = MagicMock()
main.dummy_state = MagicMock()
main.mock_client = MagicMock()

# Set a valid return value for process_action to satisfy FastAPI's response_model validation
main.engine.process_action.return_value = NarrativeResult(
    narration="Mocked narration",
    npcs=["Arthur"]
)

def test_health_check():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_chat_endpoint():
    client = TestClient(app)
    payload = {"action_text": "Hello", "current_location_id": "1"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    assert response.json()["narration"] == "Mocked narration"
