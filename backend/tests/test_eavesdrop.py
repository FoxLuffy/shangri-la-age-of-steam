"""D2: the player can overhear Nearby (present-but-not-engaged) NPCs without engaging them.
An eavesdrop action adds an EAVESDROP directive to the prompt and never pulls a named NPC
into earshot."""

from backend.models import NPC as NPCModel
from backend.models import PlayerAction
from backend.models import WorldState as WSModel
from backend.prompt_utils import build_narrative_prompt, is_eavesdrop_action


def test_is_eavesdrop_action_detection():
    assert is_eavesdrop_action("I eavesdrop on the smugglers in the corner")
    assert is_eavesdrop_action("I quietly listen in")
    assert is_eavesdrop_action("I try to overhear what they're saying")
    assert not is_eavesdrop_action("I attack the guard")
    assert not is_eavesdrop_action("I ask Silas about the cargo")


def test_eavesdrop_prompt_surfaces_nearby_without_engaging():
    nearby = NPCModel(id="silas", name="Silas", in_earshot=False, current_dialogue="The docks are watched.")
    other = NPCModel(id="mara", name="Mara", in_earshot=False)
    state = WSModel(active_npcs=[nearby, other])

    prompt = build_narrative_prompt(state, PlayerAction(action_text="I listen in on Silas and Mara"))
    assert "EAVESDROPPING" in prompt
    assert "Silas" in prompt and "Mara" in prompt
    # Their last-heard line is offered as a lead.
    assert "The docks are watched." in prompt
    # They are NOT presented as engaged/in-earshot.
    assert "In earshot (actively engaged" not in prompt


def test_non_eavesdrop_action_has_no_directive():
    nearby = NPCModel(id="silas", name="Silas", in_earshot=False)
    state = WSModel(active_npcs=[nearby])
    prompt = build_narrative_prompt(state, PlayerAction(action_text="I look around"))
    assert "EAVESDROPPING" not in prompt
