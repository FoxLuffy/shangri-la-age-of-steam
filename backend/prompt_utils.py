import os
from typing import Dict, Any
from jinja2 import Template
from backend.models import WorldState, PlayerAction

def build_narrative_prompt(state: WorldState, action: PlayerAction) -> str:
    template_path = os.path.join(os.path.dirname(__file__), "templates", "narrative_prompt.j2")
    with open(template_path, "r") as f:
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
            memories_str = str(memories_raw) if memories_raw else "None"

        npc_contexts.append({
            "name": getattr(npc, "name", "Unknown NPC"),
            "traits": getattr(npc, "traits", []) or [],
            "disposition": getattr(npc, "disposition", 0.0),
            "memories": memories_str
        })

    current_loc = getattr(state, "current_location", None)
    if current_loc is None:
        loc_id = getattr(state, "current_location_id", "Steamworks")
        loc_name = str(loc_id) if loc_id else "Steamworks"
        loc_desc = ""
    else:
        loc_name = getattr(current_loc, "name", "Steamworks")
        loc_desc = getattr(current_loc, "description", "")

    prompt_str = template.render(
        location={"name": loc_name, "description": loc_desc},
        active_npcs=active_npcs,
        npc_contexts=npc_contexts,
        action_text=action.action_text
    )

    if hasattr(action, 'mood') and action.mood:
        prompt_str += f"\n\n[Mood: {action.mood}]"
        
    if hasattr(action, 'is_exploration') and action.is_exploration:
        prompt_str += "\n\nProvide a detailed description of the surroundings."

    return prompt_str

def build_npc_interaction_prompt(
    npc1_name: str,
    npc2_name: str,
    location_name: str,
    recent_events: list[str],
    npc1_context: str,
    npc2_context: str
) -> str:
    template_path = os.path.join(os.path.dirname(__file__), "templates", "npc_interaction_prompt.j2")
    with open(template_path, "r") as f:
        template_str = f.read()
    
    template = Template(template_str)
    return template.render(
        npc1_name=npc1_name,
        npc2_name=npc2_name,
        location_name=location_name,
        recent_events=recent_events,
        npc1_context=npc1_context,
        npc2_context=npc2_context
    )
