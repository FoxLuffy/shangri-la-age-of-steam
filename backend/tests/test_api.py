import pytest
import json
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

def parse_sse_data(line: str) -> dict:
    if line and line.startswith("data: "):
        return json.loads(line.replace("data: ", "", 1))
    return {}

def test_chat_endpoint():
    client = TestClient(app)
    payload = {"action_text": "Hello", "current_location_id": "1"}
    with client.stream("POST", "/chat", json=payload) as response:
        assert response.status_code == 200
        final_result = None
        for line in response.iter_lines():
            data = parse_sse_data(line)
            if "result" in data:
                final_result = data["result"]
                
        assert final_result is not None
        assert "narration" in final_result
