import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os

def test_chat_endpoint():
    # Move imports inside the test function to ensure patching works correctly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    import main
    from main import app

    # Reset LazyEngine instance in case it was initialized by another test
    main.engine._instance = None

    # We patch main.VLLMClient so that any instantiation within main/engine uses the mock.
    with patch("main.VLLMClient") as MockClient:
        
        mock_instance = MockClient.return_value
        mock_instance.generate_stream.return_value = [
            {"choices": [{"text": "Hello! How can I help you today?"}]},
            {"choices": [{"text": "The atmosphere is heavy with steam."}]},
            {"choices": [{"text": "The Narration says: The copper pipes hiss."}], "result": "The copper pipes hiss."}
        ]
        
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
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import main
    from main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"