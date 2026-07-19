import os
from backend.models import WorldState, PlayerAction
from jinja2 import Template

def build_narrative_prompt(state: WorldState, action: PlayerAction) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "templates", "narrative_prompt.j2")
    with open(template_path, "r") as f:
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

    prompt_str = template.render(
        location=state.current_location,
        active_npcs=state.active_npcs,
        npc_contexts=npc_contexts,
        action_text=action.action_text
    )
    
    if hasattr(action, 'mood') and action.mood:
        prompt_str += f"\n\n[Mood: {action.mood}]"
        
    if hasattr(action, 'is_exploration') and action.is_exploration:
        prompt_str += "\n\nProvide a detailed description of the surroundings."
        
    return prompt_str
