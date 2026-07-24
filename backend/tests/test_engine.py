from unittest.mock import MagicMock, patch

from backend.engine import NarrativeEngine
from backend.models import NPC, Location, PlayerAction, WorldState


def test_narrative_engine_processing():
    loc = Location(id="1", name="Forest", description="A dark forest", npcs=["Orc"])
    npcs = [NPC(id="1", name="Orc", traits=["strong", "aggressive"])]
    state = WorldState(current_location_id="1", current_location=loc, active_npcs=npcs)

    mock_vllm_client = MagicMock()
    mock_vllm_client.generate_stream.return_value = [
        {"text": "You walk into the forest as steam rises.", "state_updates": {"location_id": "1"}, "events": []}
    ]

    engine = NarrativeEngine(state, mock_vllm_client)
    action = PlayerAction(action_text="I walk into the forest", current_location_id="1")

    mock_session = MagicMock()
    with patch("backend.engine.StateRepository") as MockRepoClass:
        mock_repo = MockRepoClass.return_value
        mock_repo.get_latest_state.return_value = state

        result = None
        for chunk in engine.process_action(action, mock_session):
            if isinstance(chunk, dict) and "narration" in chunk:
                result = chunk

    assert result is not None
    assert "forest" in result["narration"].lower()
