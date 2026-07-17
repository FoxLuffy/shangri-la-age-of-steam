from backend.models import WorldState, PlayerAction
from jinja2 import Template

def build_narrative_prompt(state: WorldState, action: PlayerAction) -> str:
    with open("backend/templates/narrative_prompt.j2", "r") as f:
        template_str = f.read()
    
    template = Template(template_str)
    
    npc_contexts = []
    for npc in state.active_npcs:
        memories = ", ".join([f"{m['key']}: {m['value']}" for m in npc.memories])
        memories_str = memories if memories else "None"
        npc_contexts.append({
            "name": npc.name,
            "traits": npc.traits,
            "disposition": npc.disposition,
            "memories": memories_str
        })

    return template.render(
        location=state.current_location,
        active_npcs=state.active_npcs,
        npc_contexts=npc_contexts,
        action_text=action.action_text
    )
