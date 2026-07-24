from unittest.mock import MagicMock, patch

import pytest
from backend.engine import NarrativeEngine
from backend.models import PlayerAction, WorldState


@pytest.mark.asyncio
async def test_dead_npc_removed_and_broadcasted():
    state = WorldState(current_location_id="1", active_npcs_ids=["npc_1"])

    mock_session = MagicMock()
    mock_db_state = MagicMock()
    mock_db_state.current_location_id = "1"
    mock_session.exec.return_value.first.return_value = mock_db_state

    mock_vllm_client = MagicMock()
    engine = NarrativeEngine(state, mock_vllm_client)

    # Mock parse_vllm_response to return a dead NPC
    with patch("backend.engine.parse_vllm_response") as mock_parse:
        mock_parse.return_value = (
            "The orc died.",
            {"active_npcs": [{"id": "npc_1", "name": "Orc", "traits": ["dead", "ugly"]}]},
            [],
        )

        with patch("backend.engine.StateRepository") as MockRepoClass:
            mock_repo = MockRepoClass.return_value
            mock_repo.get_latest_state.return_value = state

            # Mock create_or_update_npc to return an NPC with dead trait
            mock_npc = MagicMock()
            mock_npc.id = "npc_1"
            mock_npc.name = "Orc"
            mock_npc.traits = ["dead", "ugly"]
            mock_npc.disposition = 0.0
            mock_repo.create_or_update_npc.return_value = mock_npc

            action = PlayerAction(character_id=1, action_text="I kill the orc", current_location_id="1")

            # Execute engine process_action
            generator = engine.process_action(action, mock_session)
            last_chunk = None
            for chunk in generator:
                if isinstance(chunk, dict) and "events" in chunk:
                    last_chunk = chunk

            # Assert NPC is removed from active_npcs_ids
            assert "npc_1" not in state.active_npcs_ids

            # Assert event was added
            assert last_chunk is not None
            events = last_chunk["events"]
            npc_event = next((e for e in events if e.get("type") == "npc_state_change"), None)
            assert npc_event is not None
            assert npc_event["npc"]["id"] == "npc_1"
            assert npc_event["npc"]["hp"] == 0
