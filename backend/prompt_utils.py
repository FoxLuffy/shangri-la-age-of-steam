from backend.models import WorldState, PlayerAction
from jinja2 import Template
import os

def build_narrative_prompt(state: WorldState, action: PlayerAction) -> str:
    template_path = os.path.join(os.path.dirname(__file__), "templates", "narrative_prompt.j2")
    with open(template_path, "r") as f:
        template_str = f.read()
    
    template = Template(template_str)
    
    npc_contexts = []
    active_npcs = getattr(state, "active_npcs", []) or []
    for npc in active_npcs:
        memories = getattr(npc, "memories", [])
        if isinstance(memories, list):
            memories_list = [f"{m.get('key', '')}: {m.get('value', '')}" for m in memories if isinstance(m, dict)]
            memories_str = ", ".join(memories_list) if memories_list else "None"
        else:
            memories_str = str(memories) if memories else "None"

        npc_contexts.append({
            "name": getattr(npc, "name", "NPC"),
            "traits": getattr(npc, "traits", []),
            "disposition": getattr(npc, "disposition", 0.0),
            "memories": memories_str
        })

    loc = getattr(state, "current_location", None)
    loc_name = getattr(loc, "name", "Steamworks") if loc else "Steamworks"
    loc_desc = getattr(loc, "description", "") if loc else ""

    return template.render(
        location={"name": loc_name, "description": loc_desc},
        active_npcs=active_npcs,
        npc_contexts=npc_contexts,
        action_text=action.action_text
    )
