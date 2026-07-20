import json
from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import Session
from backend.models import WorldState, PlayerAction, NarrativeResult, Prompt, RawResponse
from backend.client import VLLMClient
from backend.prompt_utils import build_narrative_prompt
from backend.repository import StateRepository

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
            try:
                state_updates = json.loads(updates_str)
            except Exception:
                state_updates = {}
        narration = narration_clean

    # Override or supplement with direct dictionary keys if present (e.g. from mock return values)
    if isinstance(raw_data, dict):
        if raw_data.get("state_updates") is not None:
            state_updates = raw_data["state_updates"]
        if raw_data.get("events") is not None:
            events = raw_data["events"]

    return narration, state_updates, events


class NarrativeEngine:
    def __init__(self, vllm_client: VLLMClient):
        self.vllm_client = vllm_client

    def process_action(self, action: PlayerAction, session: Session) -> NarrativeResult:
        repository = StateRepository(session)

        # 1. Fetch latest world state
        state = repository.get_latest_state()

        # 2. Build template prompt
        prompt_str = build_narrative_prompt(state, action)

        # 3. Request generation from VLLM client
        raw_data = self.vllm_client.generate(prompt_str)

        # 4. Parse narrative and state updates
        narration, state_updates, events = parse_vllm_response(raw_data)

        # 5. Persist state updates if present
        if state_updates:
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

        # 6. Extract active NPC names
        active_npcs = getattr(state, "active_npcs", []) or []
        npc_names = [getattr(npc, "name", str(npc)) for npc in active_npcs]

        return NarrativeResult(
            narration=narration,
            state_updates=state_updates,
            npcs=npc_names,
            events=events
        )

