import pytest
from backend.engine import NarrativeEngine
from backend.models import WorldState, Location, NPC, PlayerAction
from unittest.mock import MagicMock

def test_narrative_engine_processing():
    # Setup dummy state
    loc = Location(id="1", name="Forest", description="A dark forest", npcs=["Orc"])
    npcs = [NPC(id="1", name="Orc", traits=["strong", "aggressive"])]
    state = WorldState(current_location=loc, active_npcs=npcs, global_event=None)
    
    # Mock VLLMClient
    mock_vllm_client = MagicMock()
    
    # Initialize engine with mock
    engine = NarrativeEngine(state, mock_vllm_client)
    action = PlayerAction(action_text="I walk into the forest", current_location_id="1")
    
    result = engine.process_action(action)
    assert "forest" in result.narration.lower()
