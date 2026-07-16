import pytest
from unittest.mock import MagicMock
from backend.engine import NarrativeEngine
from backend.models import WorldState, Location, PlayerAction
from backend.client import VLLMClient

def test_narrative_engine_vllm_call():
    loc = Location(id="1", name="Forest", description="Forest", npcs=[])
    state = WorldState(current_location=loc, active_npcs=[])
    
    # Mock the client
    mock_client = MagicMock(spec=VLLMClient)
    mock_client.generate.return_value = {"text": "The trees rustle."}
    
    engine = NarrativeEngine(state, vllm_client=mock_client)
    action = PlayerAction(action_text="Look around", current_location_id="1")
    
    result = engine.process_action(action)
    assert "trees rustle" in result.narration.lower()
