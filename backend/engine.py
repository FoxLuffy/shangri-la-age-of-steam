import json
import re
from typing import Any, Dict, Optional, List, Tuple
from sqlalchemy.orm import Session
from backend.models import WorldState, PlayerAction, NarrativeResult, Location, NPC
from backend.client import VLLMClient
import logging
from backend.prompt_utils import build_narrative_prompt, build_npc_interaction_prompt
from backend.repository import StateRepository

logger = logging.getLogger(__name__)

def parse_vllm_response(raw_data: Any) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Parses response from VLLM client into narration text, state_updates dict, and events list.
    """
    narration = ""
    state_updates: Dict[str, Any] = {}
    events: List[Dict[str, Any]] = []

    if isinstance(raw_data, dict):
        if "text" in raw_data and isinstance(raw_data["text"], str):
            narration = raw_data["text"]
        elif "choices" in raw_data and isinstance(raw_data["choices"], list) and len(raw_data["choices"]) > 0:
            choice = raw_data["choices"][0]
            if isinstance(choice, dict):
                narration = choice.get("text", "") or choice.get("message", {}).get("content", "")
        elif "narration" in raw_data:
            narration = str(raw_data["narration"])
    elif isinstance(raw_data, str):
        narration = raw_data

    # Parse [Narration] and [StateUpdates] section tags if embedded in narrative response
    if "[Narration]" in narration or "[StateUpdates]" in narration:
        parts = narration.split("[StateUpdates]")
        narration_clean = parts[0].replace("[Narration]", "").strip()

        if len(parts) > 1:
            updates_str = parts[1].strip()
            if "```" in updates_str:
                updates_str = updates_str.split("```")[1]
                if updates_str.startswith("json"):
                    updates_str = updates_str[4:]
                updates_str = updates_str.strip()
            if "[Events]" in updates_str:
                su_part, ev_part = updates_str.split("[Events]", 1)
                try:
                    state_updates = json.loads(su_part.strip())
                except Exception:
                    state_updates = {}
                try:
                    events = json.loads(ev_part.strip())
                except Exception:
                    events = []
            else:
                try:
                    state_updates = json.loads(updates_str)
                except Exception:
                    state_updates = {}
        narration = narration_clean
    else:
        # Strip out any JSON block at the end if present
        json_match = re.search(r'\{.*\}', narration, re.DOTALL)
        if json_match:
            try:
                state_updates = json.loads(json_match.group(0))
                narration = narration[:json_match.start()].strip()
            except Exception:
                pass

    # Override or supplement with direct dictionary keys if present (e.g. from mock return values)
    if isinstance(raw_data, dict):
        if raw_data.get("state_updates") is not None:
            state_updates = raw_data["state_updates"]
        if raw_data.get("events") is not None:
            events = raw_data["events"]

    return narration, state_updates, events


class NarrativeEngine:
    def __init__(self, state_or_client: Any = None, vllm_client: Optional[VLLMClient] = None):
        if isinstance(state_or_client, VLLMClient):
            self.vllm_client = state_or_client
            self.initial_state = None
        elif state_or_client is not None and not isinstance(state_or_client, VLLMClient):
            self.initial_state = state_or_client
            self.vllm_client = vllm_client if vllm_client is not None else VLLMClient()
        else:
            self.initial_state = None
            if vllm_client is None:
                raise ValueError("VLLMClient must be provided explicitly if no initial state is given.")
            self.vllm_client = vllm_client

    def process_action(self, action: PlayerAction, session: Optional[Session] = None):
        if session:
            repository = StateRepository(session)
            state = repository.get_latest_state()
        elif self.initial_state:
            repository = None
            state = self.initial_state
        else:
            repository = None
            state = WorldState(
                current_location_id="1",
                current_location=Location(id="1", name="Steamworks", description="A dark workshop.", npcs=[]),
                active_npcs=[]
            )

        prompt_str = build_narrative_prompt(state, action)

        full_raw_data = ""
        is_narrating = True
        buffer = ""
        for chunk in self.vllm_client.generate_stream(prompt_str):
            text = ""
            if isinstance(chunk, dict):
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    choice = chunk["choices"][0]
                    text = choice.get("text", "") or choice.get("delta", {}).get("content", "") or choice.get("message", {}).get("content", "")
                elif "text" in chunk:
                    text = chunk["text"]
            elif isinstance(chunk, str):
                text = chunk
                
            if text:
                full_raw_data += text
                if is_narrating:
                    if "[StateUpdates]" in full_raw_data:
                        is_narrating = False
                        continue
                    
                    buffer += text.replace("[Narration]", "")
                    # If buffer has a '[' but doesn't have the full '[StateUpdates]', we hold it.
                    if "[" in buffer:
                        # Find the first '['
                        idx = buffer.find("[")
                        # We can yield everything before '['
                        if idx > 0:
                            yield buffer[:idx]
                            buffer = buffer[idx:]
                        
                        # If buffer is a prefix of "[StateUpdates]", we must wait to see more
                        if "[StateUpdates]".startswith(buffer):
                            pass
                        else:
                            # It's not the start of [StateUpdates], safe to yield
                            yield buffer
                            buffer = ""
                    else:
                        yield buffer
                        buffer = ""
                        
        if is_narrating and buffer:
            yield buffer

        narration, state_updates, events = parse_vllm_response(full_raw_data)

        if repository and state_updates:
            loc_id = state_updates.get("location_id") or getattr(state, "current_location_id", "1")
            if "location_name" in state_updates or "location_description" in state_updates:
                loc_data = {}
                if "location_name" in state_updates:
                    loc_data["name"] = state_updates["location_name"]
                if "location_description" in state_updates:
                    loc_data["description"] = state_updates["location_description"]
                repository.update_location(loc_id, loc_data)
            
            if "active_npcs" in state_updates and isinstance(state_updates["active_npcs"], list):
                for npc_info in state_updates["active_npcs"]:
                    if isinstance(npc_info, dict):
                        repository.create_or_update_npc(npc_info, loc_id)
                        
            if "inventory_updates" in state_updates and isinstance(state_updates["inventory_updates"], list):
                for inv_update in state_updates["inventory_updates"]:
                    if isinstance(inv_update, dict):
                        repository.apply_inventory_update(inv_update)
                        
            if "quest_updates" in state_updates and isinstance(state_updates["quest_updates"], list):
                for quest_update in state_updates["quest_updates"]:
                    if isinstance(quest_update, dict):
                        repository.apply_quest_update(quest_update)

            if "faction_updates" in state_updates and isinstance(state_updates["faction_updates"], list):
                for faction_update in state_updates["faction_updates"]:
                    if isinstance(faction_update, dict):
                        repository.apply_faction_update(faction_update)

            if "combat_updates" in state_updates:
                repository.apply_combat_update(state_updates["combat_updates"])

            if "empire_updates" in state_updates:
                repository.apply_empire_update(state_updates["empire_updates"])

            if "minigame_trigger" in state_updates:
                minigame_type = state_updates["minigame_trigger"]
                if minigame_type in ["hack", "lockpick"]:
                    repository.trigger_minigame(minigame_type)

            if state_updates.get("location_id"):
                state.current_location_id = state_updates["location_id"]
                repository.save_state(state)
                
        if repository:
            repository.record_ledger_entry(
                action=action.action_text,
                narration=narration,
                state_updates=state_updates,
                events=events,
                location_id=getattr(state, "current_location_id", "1")
            )

        active_npcs = getattr(state, "active_npcs", []) or []
        npc_names = [getattr(npc, "name", str(npc)) for npc in active_npcs]

        yield {
            "narration": narration,
            "state_updates": state_updates,
            "npcs": npc_names,
            "events": events or [],
            "is_combat_active": getattr(state, "is_combat_active", False)
        }

from sqlmodel import select
from backend.database import ResourceMarket, WorldEvent, Location, NPC, get_session
from backend.repository import StateRepository
from backend.client import VLLMClient
import random
import os

async def trigger_npc_interaction(location: Location, npc1: NPC, npc2: NPC):
    """
    Generate dialogue between two NPCs in the same location and record it.
    """
    logger.info(f"Interaction resolving for {npc1.name} and {npc2.name} at {location.name}.")
    
    prompt = (
        f"You are the world engine for Shangri-la: Age of Steam. "
        f"Two NPCs are interacting at {location.name}: {location.description}.\n"
        f"NPC 1: {npc1.name}, Traits: {npc1.traits}\n"
        f"NPC 2: {npc2.name}, Traits: {npc2.traits}\n"
        f"Write a short, engaging 2-3 line dialogue between them reflecting their traits and the location."
    )
    
    client = VLLMClient()
    try:
        response = client.generate(prompt=prompt, max_tokens=150, temperature=0.8)
        dialogue = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
        if dialogue:
            with get_session() as session:
                repo = StateRepository(session)
                repo.record_ledger_entry(
                    action=f"Overheard interaction between {npc1.name} and {npc2.name}",
                    narration=dialogue,
                    location_id=location.id
                )
            logger.info(f"Recorded NPC interaction at {location.name}")
            
            # Broadcast to clients
            try:
                from backend.main import manager
                import json
                await manager.broadcast(json.dumps({
                    "type": "narrative_event",
                    "data": {
                        "narration": f"[NPC Interaction] {dialogue}",
                        "state_updates": {},
                        "events": []
                    },
                    "action": {
                        "action_text": f"Overheard {npc1.name} and {npc2.name}",
                        "client_id": "system"
                    }
                }))
            except Exception as e:
                logger.error(f"Failed to broadcast NPC interaction: {e}")
                
    except Exception as e:
        logger.error(f"Failed to generate NPC interaction: {e}")

async def scan_locations_and_trigger_interactions():
    """
    Background logic to scan locations and trigger NPC-to-NPC interactions.
    """
    logger.info("Scanning locations for NPC interactions...")
    with get_session() as session:
        locations = session.exec(select(Location)).all()
        for loc in locations:
            npcs_in_loc = session.exec(select(NPC).where(NPC.location_id == loc.id)).all()
            if len(npcs_in_loc) > 1:
                # 30% chance for an interaction to happen if there are multiple NPCs
                if random.random() < 0.3:
                    npc1, npc2 = random.sample(npcs_in_loc, 2)
                    logger.info(f"Triggering interaction at location {loc.id} between {npc1.name} and {npc2.name}")
                    await trigger_npc_interaction(loc, npc1, npc2)

def simulate_economy_tick(session: Session):
    """
    Simulate the economy tick by fluctuating prices based on base price, volatility, and active world events.
    """
    import random
    
    # Get active events
    active_events = session.exec(select(WorldEvent).where(WorldEvent.is_active == 1)).all()
    
    # Aggregate modifiers from events
    modifiers = {}
    for event in active_events:
        for resource, impact in event.faction_impacts.items():
            if resource not in modifiers:
                modifiers[resource] = 1.0
            # Severity scales the impact
            modifiers[resource] += (impact * event.severity)
            
    markets = session.exec(select(ResourceMarket)).all()
    
    for market in markets:
        # Base random fluctuation based on volatility
        fluctuation = 1.0 + random.uniform(-market.volatility, market.volatility)
        
        # Apply event modifiers if any
        modifier = modifiers.get(market.resource_name, 1.0)
        
        # Calculate new price
        market.current_price = max(1.0, market.current_price * fluctuation * modifier)
        
        # Trend back towards base price slightly if no extreme events
        if modifier == 1.0:
            market.current_price += (market.base_price - market.current_price) * 0.05
            
        session.add(market)
    session.commit()

async def world_tick():
    """
    Runs the world simulation tick.
    """
    logger.info("World tick started.")
    await scan_locations_and_trigger_interactions()
    
    from backend.database import get_session, Property, Character
    with get_session() as session:
        simulate_economy_tick(session)
        
        # Passive Income Generation
        char_id = 1
        char = session.get(Character, char_id)
        if char:
            properties = session.exec(select(Property).where(Property.owner_id == char_id)).all()
            total_income = sum(p.income_per_tick for p in properties)
            if total_income > 0:
                char.brass_coins += total_income
                session.add(char)
                session.commit()
                logger.info(f"Passive income generated: {total_income} coins for Character {char_id}")
        
    logger.info("World tick completed.")
