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
        for chunk in self.vllm_client.generate_stream(prompt_str):
            text = ""
            if isinstance(chunk, dict):
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    choice = chunk["choices"][0]
                    text = choice.get("text", "") or choice.get("message", {}).get("content", "")
                elif "text" in chunk:
                    text = chunk["text"]
            elif isinstance(chunk, str):
                text = chunk
                
            if text:
                full_raw_data += text
                yield text

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

            if state_updates.get("location_id"):
                state.current_location_id = state_updates["location_id"]
                repository.save_state(state)

        active_npcs = getattr(state, "active_npcs", []) or []
        npc_names = [getattr(npc, "name", str(npc)) for npc in active_npcs]

        yield {
            "narration": narration,
            "state_updates": state_updates,
            "npcs": npc_names,
            "events": events or []
        }

async def trigger_npc_interaction(location_id: int, npc_ids: List[int]):
    """
    Placeholder for triggering and processing an interaction.
    """
    # e.g., generate dialogue, create WorldEvent
    logger.info(f"Interaction resolved for NPCs {npc_ids} at location {location_id}.")

async def scan_locations_and_trigger_interactions():
    """
    Background logic to scan locations and trigger NPC-to-NPC interactions.
    """
    logger.info("Scanning locations for NPC interactions...")
    # Mock fetching locations with multiple NPCs
    locations_with_npcs = [
        {"location_id": 1, "npcs": [101, 102]},
        {"location_id": 2, "npcs": [201]}
    ]

    for loc in locations_with_npcs:
        if len(loc["npcs"]) > 1:
            logger.info(f"Triggering interaction at location {loc['location_id']} between NPCs {loc['npcs']}")
            # Here we would normally build the prompt using prompt_utils
            # and call the LLM, then save a WorldEvent to the database.
            await trigger_npc_interaction(loc["location_id"], loc["npcs"])

async def world_tick():
    """
    Runs the world simulation tick.
    """
    logger.info("World tick started.")
    await scan_locations_and_trigger_interactions()
    logger.info("World tick completed.")
