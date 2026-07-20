from backend.models import WorldState, PlayerAction
from jinja2 import Template
from typing import Dict, Any

def build_narrative_prompt(state: WorldState, action: PlayerAction) -> str:
    with open("backend/templates/narrative_prompt.j2", "r") as f:
        template_str = f.read()
    
    template = Template(template_str)
    
    npc_contexts = []
    active_npcs = getattr(state, "active_npcs", None) or []
    for npc in active_npcs:
        memories_raw = getattr(npc, "memories", []) or []
        if isinstance(memories_raw, list):
            memories_list = []
            for m in memories_raw:
                if isinstance(m, dict):
                    memories_list.append(f"{m.get('key', '')}: {m.get('value', '')}")
                else:
                    memories_list.append(str(m))
            memories_str = ", ".join(memories_list) if memories_list else "None"
        else:
            memories_str = str(memories_raw)

        npc_contexts.append({
            "name": getattr(npc, "name", "Unknown NPC"),
            "traits": getattr(npc, "traits", []) or [],
            "disposition": getattr(npc, "disposition", 0.0),
            "memories": memories_str
        })

    current_loc = getattr(state, "current_location", None)
    if current_loc is None:
        loc_id = getattr(state, "current_location_id", "Unknown Location")
        current_loc = type("Location", (), {"name": str(loc_id), "description": "Unknown description"})()

    prompt_str = template.render(
        location=current_loc,
        active_npcs=active_npcs,
        npc_contexts=npc_contexts,
        action_text=action.action_text
    )

    if hasattr(action, 'mood') and action.mood:
        prompt_str += f"\n\n[Mood: {action.mood}]"
        
    if hasattr(action, 'is_exploration') and action.is_exploration:
        prompt_str += "\n\nProvide a detailed description of the surroundings."

    return prompt_str

