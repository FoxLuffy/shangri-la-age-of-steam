import pytest
from backend.engine import NarrativeEngine
from backend.models import WorldState, Location, NPC, PlayerAction
from unittest.mock import MagicMock

def test_narrative_engine_processing():
    loc = Location(id="1", name="Forest", description="A dark forest", npcs=["Orc"])
    npcs = [NPC(id="1", name="Orc", traits=["strong", "aggressive"])]
    state = WorldState(current_location_id="1", current_location=loc, active_npcs=npcs)
    
    mock_vllm_client = MagicMock()
    mock_vllm_client.generate.return_value = {"text": "You walk into the forest as steam rises."}
    
    engine = NarrativeEngine(state, mock_vllm_client)
    action = PlayerAction(action_text="I walk into the forest", current_location_id="1")
    
    result = engine.process_action(action)
    assert "forest" in result.narration.lower()
