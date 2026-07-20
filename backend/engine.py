import json
import re
from typing import Any, Dict, Optional, List
from sqlalchemy.orm import Session
from backend.models import WorldState, PlayerAction, NarrativeResult, RawResponse, Location, NPC
from backend.client import VLLMClient
from backend.prompt_utils import build_narrative_prompt
from backend.repository import StateRepository

def parse_llm_output(raw_text: str) -> Dict[str, Any]:
    narration = raw_text
    state_updates = None
    events = None

    if "[Narration]" in raw_text:
        parts = raw_text.split("[Narration]")
        after_narr = parts[-1]
        if "[StateUpdates]" in after_narr:
            narr_part, rest = after_narr.split("[StateUpdates]", 1)
            narration = narr_part.strip()
            
            if "[Events]" in rest:
                su_part, ev_part = rest.split("[Events]", 1)
                try:
                    state_updates = json.loads(su_part.strip())
                except Exception:
                    pass
                try:
                    events = json.loads(ev_part.strip())
                except Exception:
                    pass
            else:
                try:
                    state_updates = json.loads(rest.strip())
                except Exception:
                    pass
        else:
            narration = after_narr.strip()
    else:
        # Strip out any JSON block at the end if present
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            narration = raw_text[:json_match.start()].strip()
            try:
                state_updates = json.loads(json_match.group(0))
            except Exception:
                pass

    return {
        "narration": narration if narration else raw_text,
        "state_updates": state_updates,
        "events": events
    }

class NarrativeEngine:
    def __init__(self, state_or_client: Any = None, vllm_client: Optional[VLLMClient] = None):
        if isinstance(state_or_client, VLLMClient):
            self.vllm_client = state_or_client
            self.initial_state = None
        else:
            self.initial_state = state_or_client
            self.vllm_client = vllm_client or VLLMClient()

    def process_action(self, action: PlayerAction, session: Optional[Session] = None) -> NarrativeResult:
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
        
        if hasattr(action, 'mood') and action.mood:
            prompt_str += f"\n\n[Mood: {action.mood}]"
            
        if hasattr(action, 'is_exploration') and action.is_exploration:
            prompt_str += "\n\nProvide a detailed description of the surroundings."
        
        raw_data = self.vllm_client.generate(prompt_str)

        if isinstance(raw_data, dict):
            if "text" in raw_data and not any(k in raw_data for k in ["narration", "choices"]):
                parsed = parse_llm_output(raw_data["text"])
                narration = parsed["narration"]
                state_updates = raw_data.get("state_updates") or parsed["state_updates"]
                events = raw_data.get("events") or parsed["events"]
            elif "choices" in raw_data and len(raw_data["choices"]) > 0:
                raw_text = raw_data["choices"][0].get("text", "")
                parsed = parse_llm_output(raw_text)
                narration = parsed["narration"]
                state_updates = parsed["state_updates"]
                events = parsed["events"]
            elif "narration" in raw_data:
                narration = raw_data["narration"]
                state_updates = raw_data.get("state_updates")
                events = raw_data.get("events")
            else:
                raw_text = str(raw_data.get("text", raw_data))
                parsed = parse_llm_output(raw_text)
                narration = parsed["narration"]
                state_updates = parsed["state_updates"]
                events = parsed["events"]
        else:
            narration = str(raw_data)
            state_updates = None
            events = None

        if repository and state_updates:
            if "location_id" in state_updates:
                repository.update_location(state_updates["location_id"], state_updates)
                state.current_location_id = state_updates["location_id"]
            repository.save_state(state)

        active_npc_names = []
        if hasattr(state, 'active_npcs') and state.active_npcs:
            active_npc_names = [npc.name for npc in state.active_npcs if hasattr(npc, 'name')]

        return NarrativeResult(
            narration=narration,
            state_updates=state_updates,
            npcs=active_npc_names,
            events=events or []
        )
