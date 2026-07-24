import pytest
from backend.models import Location, PlayerAction, WorldState
from backend.prompt_utils import build_narrative_prompt


def test_repetitive_narration_prompt_rule():
    location = Location(id="loc-1", name="The Rusty Tankard", description="A dim, steam-filled tavern.", npcs=[])
    state = WorldState(current_location_id="loc-1", current_location=location, active_npcs=[])
    action = PlayerAction(action_text="I sit at the bar.", current_location_id="loc-1")

    prompt = build_narrative_prompt(state, action)

    # Check that the new rule is included in the prompt
    assert "Environment Descriptions" in prompt
    assert (
        "Omit general environmental descriptions on subsequent turns in the same location unless the environment has meaningfully changed."
        in prompt
    )


if __name__ == "__main__":
    pytest.main([__file__])
