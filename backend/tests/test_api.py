import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

# Mocking the engine and clients
# In a real test, we'd use more sophisticated mocking, but this is for a basic connectivity check
import main
main.engine = MagicMock()
main.dummy_state = MagicMock()
main.mock_client = MagicMock()

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_chat_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {"action_text": "Hello", "current_location_id": "1"}
        response = await ac.post("/chat", json=payload)
        assert response.status_code == 200
