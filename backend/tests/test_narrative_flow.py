import pytest
from unittest.mock import MagicMock, patch
from backend.engine import NarrativeEngine
from backend.models import WorldState, Location, PlayerAction
from backend.client import VLLMClient

def test_narrative_engine_vllm_call():
    loc = Location(id="1", name="Forest", description="Forest", npcs=[])
    state = WorldState(current_location_id="1", current_location=loc, active_npcs=[])
    
    mock_client = MagicMock(spec=VLLMClient)
    mock_client.generate_stream.return_value = [
        {
            "text": "The trees rustle.",
            "state_updates": {"location_id": "1"},
            "events": []
        }
    ]
    
    engine = NarrativeEngine(state, mock_client)
    action = PlayerAction(action_text="Look around", current_location_id="1")
    
    mock_session = MagicMock()
    with patch("backend.engine.StateRepository") as MockRepoClass:
        mock_repo = MockRepoClass.return_value
        mock_repo.get_latest_state.return_value = state
        
        result = None
        for chunk in engine.process_action(action, mock_session):
            if isinstance(chunk, dict) and "narration" in chunk:
                result = chunk
        
    assert result is not None
    assert "trees rustle" in result["narration"].lower()
