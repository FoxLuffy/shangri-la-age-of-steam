import pytest
from backend.models import WorldState, PlayerAction, Location, NPC
from backend.prompt_utils import build_narrative_prompt

def test_flavor_prompt_complex_inputs():
    # Create a world state with 5+ NPCs
    npcs = [
        NPC(id="1", name="Guard 1", traits=["brave", "tired"]),
        NPC(id="2", name="Guard 2", traits=["alert"]),
        NPC(id="3", name="Merchant", traits=["greedy", "friendly"]),
        NPC(id="4", name="Spy", traits=["sneaky", "silent"]),
        NPC(id="5", name="Thief", traits=["fast", "hungry"]),
        NPC(id="6", name="Beggar", traits=["pitiful"])
    ]
        
    location = Location(id="loc-1", name="The Rusty Tankard", description="A dim, steam-filled tavern.", npcs=[])
    state = WorldState(current_location=location, active_npcs=npcs)
        
    # Create a long action string (over 200 chars)
    long_action = (
        "The player cautiously approaches the bar counter, their boots clanking against the wet floor. "
        "They take a deep breath, feeling the heavy, metallic scent of steam and old grease. "
        "With a trembling hand, they reach for a tarnished brass mug, trying not to let their "
        "reflection in the polished wood show their fear. They want to ask for a drink but are "
        "terrified of the man watching them from the corner."
    )
        
    # Test with mood and exploration
    action = PlayerAction(
        action_text=long_action, 
        current_location_id="loc-1", 
        mood="tense", 
        is_exploration=True
    )
        
    # Build the prompt
    prompt = build_narrative_prompt(state, action)
        
    # Assertions
    assert "The Rusty Tankard" in prompt
    assert "dim, steam-filled tavern" in prompt
        
    # Check if all 6 NPCs are mentioned in the prompt
    for npc in npcs:
        assert npc.name in prompt
            
    # Check if the action text is present
    assert "reflection in the polished wood" in prompt
        
    # Check for mood and exploration instructions
    assert "[Mood: tense]" in prompt
    assert "Provide a detailed description of the surroundings" in prompt
        
    # Check for system instructions
    assert "you are the narrator" in prompt.lower()
    assert "describe the immediate results" in prompt.lower()

if __name__ == "__main__":
    pytest.main([__file__])
