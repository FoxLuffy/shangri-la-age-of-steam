from fastapi.testclient import TestClient
from backend.main import app, manager
from unittest.mock import patch
import json
import asyncio

def test_chat_minigame_trigger_broadcast():
    client = TestClient(app)
    
    with patch("backend.main.engine.process_action") as mock_process, \
         patch("backend.main.manager.broadcast") as mock_broadcast:
        
        mock_process.return_value = [{"narration": "You hack.", "state_updates": {"minigame_trigger": "hack"}, "events": []}]
        
        action = {"action_text": "I hack the terminal", "current_location_id": "1", "character_id": 1}
        response = client.post("/chat", json=action)
        
        assert response.status_code == 200
        
        # consume SSE
        list(response.iter_lines())
        
        called_args = []
        for call in mock_broadcast.call_args_list:
            called_args.append(call[0][0])
            
        found_trigger = False
        for arg in called_args:
            data = json.loads(arg)
            if data.get("type") == "trigger_minigame" and data.get("minigame_type") == "hack":
                found_trigger = True
                
        assert found_trigger
