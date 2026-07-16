from backend.models import WorldState, PlayerAction

def build_narrative_prompt(state: WorldState, action: PlayerAction) -> str:
    return f"""
    World State: {state.current_location.description}
    Current Action: {action.action_text}
    
    Generate a narrative description of what happens next.
    """
