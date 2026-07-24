import json
import os
import sys
from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def test_chat_endpoint():
    # Move imports inside the test function to ensure patching works correctly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    from backend.client import VLLMClient
    from backend.engine import NarrativeEngine

    import main
    from main import app

    mock_vllm = MagicMock(spec=VLLMClient)
    mock_vllm.generate_stream.return_value = [
        {"choices": [{"text": "Hello! How can I help you today?"}]},
        {"choices": [{"text": "The atmosphere is heavy with steam."}]},
        {"choices": [{"text": "The Narration says: The copper pipes hiss."}], "result": "The copper pipes hiss."},
    ]
    main.engine._instance = NarrativeEngine(mock_vllm)

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


def parse_sse_data(line: str) -> dict:
    if line and line.startswith("data: "):
        return json.loads(line.replace("data: ", "", 1))
    return {}


def test_health_check():
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
