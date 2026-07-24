import pytest
from unittest.mock import patch, MagicMock
from backend.models import PlayerAction, WorldState
from backend.database import WorldEvent
from backend.prompt_utils import build_narrative_prompt

@patch("backend.prompt_utils.get_session")
def test_gossip_engine_injection(mock_get_session):
    # Setup mock DB session
    mock_session = MagicMock()
    mock_event = WorldEvent(id=1, event_text="The Copper shortage has begun!", is_active=1)
    mock_session.exec.return_value.all.return_value = [mock_event]
    mock_get_session.return_value.__enter__.return_value = mock_session

    state = WorldState()
    action = PlayerAction(action_text="I ask about the news.", current_location_id="1")
    
    prompt = build_narrative_prompt(state, action)
    
    assert "Current World Gossip / Recent Rumors:" in prompt
    assert "The Copper shortage has begun!" in prompt
