import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from backend.models import NarrativeResult

# Mocking the engine and clients
# In a real test, we'd use more sophisticated mocking, but this is for a basic connectivity check
import main
main.engine = MagicMock()
main.engine.process_action.return_value = NarrativeResult(
    narration="Hello",
    state_updates={},
    npcs="",
    active_npcs=[],
    events=[]
)
main.dummy_state = MagicMock()
main.mock_client = MagicMock()

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_chat_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"action_text": "Hello", "current_location_id": "1"}
        response = await ac.post("/chat", json=payload)
        assert response.status_code == 200
