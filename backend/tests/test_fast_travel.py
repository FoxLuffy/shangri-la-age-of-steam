from unittest.mock import MagicMock, patch

from backend.engine import NarrativeEngine
from backend.models import Location, PlayerAction, WorldState


def test_fast_travel_syncs_location_id():
    # Setup state
    loc_old = Location(id="1", name="Forest", description="Old location", npcs=[])
    state = WorldState(current_location_id="1", current_location=loc_old, active_npcs=[])

    mock_vllm_client = MagicMock()
    mock_vllm_client.generate_stream.return_value = [
        {"text": "You traveled safely.", "state_updates": {}, "events": []}
    ]

    engine = NarrativeEngine(state, mock_vllm_client)

    # Action asks to fast travel to "2"
    action = PlayerAction(action_text="Fast travel to city", current_location_id="2", character_id=1)

    mock_session = MagicMock()
    # Mock the character
    mock_char = MagicMock()
    mock_char.location_id = "1"

    # Mock the location object that the engine will fetch
    mock_loc2 = MagicMock()
    mock_loc2.id = "2"
    mock_loc2.name = "City"
    mock_loc2.description = "A grand city"
    mock_loc2.npcs = []

    # Mock the db state
    mock_db_state = MagicMock()
    mock_db_state.current_location_id = "1"

    def mock_get(model, id):
        from backend.database import Character
        from backend.database import Location as DBLocation

        if model == Character:
            return mock_char
        elif model == DBLocation:
            return mock_loc2
        return None

    mock_session.get = mock_get

    def mock_exec(query):
        mock_result = MagicMock()
        mock_result.first.return_value = mock_db_state
        return mock_result

    mock_session.exec = mock_exec

    with patch("backend.engine.StateRepository") as MockRepoClass:
        mock_repo = MockRepoClass.return_value
        # Important: the repository would return the state
        mock_repo.get_latest_state.return_value = state

        for chunk in engine.process_action(action, mock_session):
            if isinstance(chunk, dict) and "narration" in chunk:
                pass

        # The character's location_id should have been updated before fetching state
        assert mock_char.location_id == "2"
        # The db_state's current_location_id should have been updated too
        assert mock_db_state.current_location_id == "2"
