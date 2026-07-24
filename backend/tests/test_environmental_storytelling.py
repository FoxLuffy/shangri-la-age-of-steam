from backend.models import Location, PlayerAction, WorldState
from backend.prompt_utils import build_narrative_prompt


def test_environmental_storytelling_low_condition():
    loc = Location(id="1", name="Steamworks", description="A noisy place.", condition=20)
    state = WorldState(current_location=loc, current_location_id="1")
    action = PlayerAction(action_text="look around")

    prompt = build_narrative_prompt(state, action)

    assert "**Condition:** 20/100" in prompt
    assert "crumbling walls" in prompt

def test_environmental_storytelling_high_condition():
    loc = Location(id="2", name="High Society", description="A fancy place.", condition=85)
    state = WorldState(current_location=loc, current_location_id="2")
    action = PlayerAction(action_text="look around")

    prompt = build_narrative_prompt(state, action)

    assert "**Condition:** 85/100" in prompt
    assert "polished brass facades" in prompt

def test_environmental_storytelling_avg_condition():
    loc = Location(id="3", name="Average Joe", description="An average place.", condition=50)
    state = WorldState(current_location=loc, current_location_id="3")
    action = PlayerAction(action_text="look around")

    prompt = build_narrative_prompt(state, action)

    assert "**Condition:** 50/100" in prompt
    assert "mix of typical wear-and-tear" in prompt
