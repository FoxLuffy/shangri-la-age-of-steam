from backend.models import Location, PlayerAction, WorldState
from backend.prompt_utils import build_narrative_prompt


def test_exploration_context():
    state = WorldState(
        current_location_id="1", current_location=Location(id="1", name="Steamworks", description="A dark workshop.")
    )
    action = PlayerAction(action_text="Look around", current_location_id="1", context_type="Exploration")

    prompt = build_narrative_prompt(state, action)

    assert "[Context: Exploration]" in prompt
    assert "verbose and elaborate" in prompt


def test_dialogue_context():
    state = WorldState(
        current_location_id="1", current_location=Location(id="1", name="Steamworks", description="A dark workshop.")
    )
    action = PlayerAction(action_text="Talk to Barnaby", current_location_id="1", context_type="Dialogue")

    prompt = build_narrative_prompt(state, action)

    assert "[Context: Dialogue]" in prompt
    assert "short and punchy" in prompt
