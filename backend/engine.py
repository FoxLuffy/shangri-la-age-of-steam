from backend.models import WorldState, PlayerAction, NarrativeResult, Prompt, RawResponse
from backend.client import VLLMClient
from backend.prompt_utils import build_narrative_prompt
from backend.repository import StateRepository
import json
from typing import Any, Dict
from sqlalchemy.orm import Session
from backend.database import get_session

def parse_llm_response(raw_text: str) -> Dict[str, Any]:
    narration = ""
    state_updates = {}
    events = []
    
    if "[Narration]" in raw_text:
        parts = raw_text.split("[Narration]")
        remaining = parts[1]
        if "[StateUpdates]" in remaining:
            narr_part, state_part = remaining.split("[StateUpdates]")
            narration = narr_part.strip()
            try:
                start_idx = state_part.find('{')
                end_idx = state_part.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = state_part[start_idx:end_idx+1]
                    state_updates = json.loads(json_str)
            except Exception as e:
                print(f"Error parsing StateUpdates JSON: {e}")
        else:
            narration = remaining.strip()
    else:
        narration = raw_text.strip()
        
    return {
        "text": narration,
        "state_updates": state_updates,
        "events": events
    }

class NarrativeEngine:
    def __init__(self, vllm_client: VLLMClient):
        self.vllm_client = vllm_client

    def process_action(self, action: PlayerAction, session: Session) -> NarrativeResult:
        # Use the repository with the provided session
        repository = StateRepository(session)
        
        # 1. Get the latest state
        state = repository.get_latest_state()
        if not state:
            raise ValueError("No world state found in the database. Ensure database is seeded.")
        
        # 2. Build prompt using prompt_utils
        prompt_str = build_narrative_prompt(state, action)
        
        # 3. Call vllm_client.generate()
        raw_data = self.vllm_client.generate(prompt_str)
        
        # Extract text content from raw_data (handles choices vs direct dict format)
        if "choices" in raw_data and len(raw_data["choices"]) > 0:
            full_text = raw_data["choices"][0].get("text", "")
        else:
            full_text = raw_data.get("text", "")
            
        parsed = parse_llm_response(full_text)
        
        # Merge manual overrides from mock if present
        if "state_updates" in raw_data and raw_data["state_updates"]:
            parsed["state_updates"] = raw_data["state_updates"]
        if "events" in raw_data and raw_data["events"]:
            parsed["events"] = raw_data["events"]
            
        raw_response = RawResponse(**parsed)
        
        # 4. Parse result
        narration = raw_response.text
        
        # 5. Update state
        state_updates = raw_response.state_updates
        if state_updates:
            if "location_id" in state_updates:
                new_loc_id = state_updates["location_id"]
                repository.update_location(new_loc_id, state_updates)
                state.current_location_id = new_loc_id
            
            if "active_npcs" in state_updates:
                npc_ids = []
                for npc_data in state_updates["active_npcs"]:
                    if isinstance(npc_data, dict) and "id" in npc_data:
                        npc_ids.append(npc_data["id"])
                    elif isinstance(npc_data, str):
                        npc_ids.append(npc_data)
                if npc_ids:
                    state.active_npcs_ids = npc_ids
            
            # Save the updated state
            repository.save_state(state)
        
        # 6. Handle Dynamic Events
        events = []
        if raw_response.events:
            events = raw_response.events
            print(f"Dynamic Events Triggered: {events}")
        
        active_npcs_names = []
        if hasattr(state, 'active_npcs') and state.active_npcs:
            active_npcs_names = [npc.name for npc in state.active_npcs]
            
        return NarrativeResult(
            narration=narration,
            state_updates=state_updates,
            npcs=active_npcs_names,
            events=events
        )
