from backend.models import WorldState, PlayerAction
from jinja2 import Template

def build_narrative_prompt(state: WorldState, action: PlayerAction) -> str:
    with open("backend/templates/narrative_prompt.j2", "r") as f:
        template_str = f.read()
    
    template = Template(template_str)
    
    return template.render(
        location=state.current_location,
        active_npcs=state.active_npcs,
        action_text=action.action_text
    )
