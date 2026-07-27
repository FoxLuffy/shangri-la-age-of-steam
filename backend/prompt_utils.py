import os
from typing import Optional

from backend.database import WorldEvent, get_session
from backend.models import Location, PlayerAction, WorldState
from jinja2 import Template
from sqlmodel import select


def get_dynamic_narration(
    action: Optional[PlayerAction] = None, location: Optional[Location] = None, world_state: Optional[WorldState] = None
) -> str:
    """
    Provides a context-aware description based on user actions and location.
    """
    if action is None and location is None and world_state is None:
        return "[Narration]The environment remains still, but the air is heavy with the weight of history."

    if action:
        return f"[Narration]As you {action.action_text.lower()}, the surrounding details shift."

    if location:
        return f"[Narration]You are in {location.name}. {location.description}"

    if world_state and world_state.current_location:
        return f"[Narration]The current setting is {world_state.current_location.name}."

    return "[Narration]The atmosphere is thick with mystery."


def build_narrative_prompt(state: WorldState, action: PlayerAction, ghost_echoes: list = None) -> str:
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

        disp = getattr(npc, "disposition", 0.0)
        custom_prompt = getattr(npc, "custom_system_prompt", None) or ""
        if disp >= 0.9:
            custom_prompt = (custom_prompt + " Act like a loyal ally, be extremely helpful, and share secrets.").strip()
        elif disp <= -0.6:
            custom_prompt = (custom_prompt + " Actively work against the player, raise prices, and refuse service.").strip()

        npc_contexts.append(
            {
                "id": getattr(npc, "id", None),
                "name": getattr(npc, "name", "Unknown NPC"),
                "traits": getattr(npc, "traits", []) or [],
                "disposition": disp,
                "memories": memories_str,
                "faction_id": getattr(npc, "faction_id", None),
                "hp": getattr(npc, "hp", 100),
                "max_hp": getattr(npc, "max_hp", 100),
                "armor": getattr(npc, "armor", 0),
                "status_effects": getattr(npc, "status_effects", []) or [],
                "custom_system_prompt": custom_prompt if custom_prompt else None,
                "in_earshot": bool(getattr(npc, "in_earshot", False)),
            }
        )

    current_loc = getattr(state, "current_location", None)
    loc_id = getattr(state, "current_location_id", "1")
    if current_loc is None:
        loc_name = str(loc_id) if loc_id else "Steamworks"
        loc_desc = ""
    else:
        loc_name = getattr(current_loc, "name", "Steamworks")
        loc_desc = getattr(current_loc, "description", "")

    all_properties = getattr(state, "properties", [])
    player_id = getattr(getattr(state, "player_stats", None), "id", None)

    location_properties = [p for p in all_properties if str(p.location_id) == str(loc_id)]
    player_properties = [p for p in all_properties if p.owner_id == player_id] if player_id else []

    recent_events = []
    try:
        with get_session() as session:
            events = session.exec(
                select(WorldEvent)
                .where(WorldEvent.is_active == 1)
                .order_by(WorldEvent.id.desc())
                .limit(3)
            ).all()
            for event in events:
                recent_events.append(event.event_text)
    except Exception:
        pass

    prompt_str = template.render(
        location={"name": loc_name, "description": loc_desc, "condition": getattr(current_loc, "condition", 50)},
        active_npcs=active_npcs,
        npc_contexts=npc_contexts,
        action_text=action.action_text,
        inventory=getattr(state, "inventory", []),
        quests=getattr(state, "quests", []),
        factions=getattr(state, "factions", []),
        player_stats=getattr(state, "player_stats", None),
        is_combat_active=getattr(state, "is_combat_active", False),
        brass_coins=getattr(state, "brass_coins", 0),
        location_properties=location_properties,
        player_properties=player_properties,
        ghost_echoes=ghost_echoes,
        character_name=getattr(getattr(state, "player_stats", None), "name", "Traveler"),
        recent_events=recent_events,
        time_period=getattr(state, "time_period", "Day"),
        weather=getattr(state, "weather", "Clear"),
        season=getattr(state, "season", "Brass Festival"),
        main_quest=getattr(state, "main_quest", None),
        active_bounty=getattr(state, "active_bounty", None),
    )

    if hasattr(action, "mood") and action.mood:
        prompt_str += f"\n\n[Mood: {action.mood}]"

    if hasattr(action, "context_type") and action.context_type:
        if action.context_type.lower() == "exploration":
            prompt_str += "\n\n[Context: Exploration] Provide a detailed and atmospheric description of the new surroundings. Feel free to be verbose and elaborate on the scenery."
        elif action.context_type.lower() == "dialogue":
            prompt_str += "\n\n[Context: Dialogue] Keep the narration short and punchy. Focus on the immediate interaction and character responses without lengthy environmental descriptions."
        else:
            prompt_str += f"\n\n[Context: {action.context_type}] Adjust your verbosity and focus accordingly."
    elif hasattr(action, "is_exploration") and action.is_exploration:
        prompt_str += "\n\n[Context: Exploration] Provide a detailed and atmospheric description of the new surroundings. Feel free to be verbose and elaborate on the scenery."

    return prompt_str


def build_npc_interaction_prompt(
    npc1_name: str,
    npc2_name: str,
    location_name: str,
    recent_events: list[str],
    npc1_context: str,
    npc2_context: str,
    active_event_descriptions: Optional[list[str]] = None,
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
        npc2_context=npc2_context,
        active_event_descriptions=active_event_descriptions or [],
    )
