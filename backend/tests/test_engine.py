from backend.engine import NarrativeEngine
from backend.models import WorldState, Location, NPC, PlayerAction
from unittest.mock import MagicMock, patch

def test_narrative_engine_processing():
    # Setup dummy state
    loc = Location(id="1", name="Forest", description="A dark forest", npcs=["Orc"])
    npcs = [NPC(id="1", name="Orc", traits=["strong", "aggressive"])]
    state = WorldState(current_location=loc, active_npcs=npcs, global_event=None)
    
    # Mock VLLMClient
    mock_vllm_client = MagicMock()
    mock_vllm_client.generate.return_value = {
        "text": "The player walks into the dark forest.",
        "state_updates": {"location_id": "1"},
        "events": []
    }
    
    # Initialize engine with mock client
    engine = NarrativeEngine(mock_vllm_client)
    action = PlayerAction(action_text="I walk into the forest", current_location_id="1")
    
    mock_session = MagicMock()
    with patch("backend.engine.StateRepository") as MockRepoClass:
        mock_repo = MockRepoClass.return_value
        mock_repo.get_latest_state.return_value = state
        
        result = engine.process_action(action, mock_session)
        
    assert "forest" in result.narration.lower()
