from backend.models import WorldState, PlayerAction, NarrativeResult, Prompt, RawResponse
from backend.client import VLLMClient
from backend.prompt_utils import build_narrative_prompt
from backend.repository import StateRepository
import json
from typing import Any
from sqlalchemy.orm import Session as SQLModelSession
from backend.database import get_session, NPC
from sqlmodel import select

def parse_llm_response(raw_text: str) -> dict:
    narration = ""
    state_updates = {}
    
    if "[Narration]" in raw_text:
        parts = raw_text.split("[Narration]", 1)[1]
        if "[StateUpdates]" in parts:
            narration_part, state_part = parts.split("[StateUpdates]", 1)
            narration = narration_part.strip()
            try:
                state_updates = json.loads(state_part.strip())
            except Exception as e:
                print(f"Error parsing StateUpdates JSON: {e}")
        else:
            narration = parts.strip()
    else:
        if "[StateUpdates]" in raw_text:
            narration, state_part = raw_text.split("[StateUpdates]", 1)
            narration = narration.strip()
            try:
                state_updates = json.loads(state_part.strip())
            except Exception as e:
                print(f"Error parsing StateUpdates JSON: {e}")
        else:
            narration = raw_text.strip()
            
    return {
        "text": narration,
        "state_updates": state_updates,
        "events": []
    }

class NarrativeEngine:
    def __init__(self, *args, **kwargs):
        # Support various initialization signatures:
        # 1. NarrativeEngine(vllm_client)
        # 2. NarrativeEngine(state, vllm_client)
        # 3. NarrativeEngine(state, vllm_client=mock_client)
        vllm_client = kwargs.get("vllm_client", None)
        state = kwargs.get("state", None)

        if args:
            first_arg = args[0]
            if hasattr(first_arg, "generate") or hasattr(first_arg, "_spec_class"):
                vllm_client = first_arg
                if len(args) > 1:
                    state = args[1]
            else:
                state = first_arg
                if len(args) > 1:
                    vllm_client = args[1]

        self.vllm_client = vllm_client
        self.session_factory = get_session

        if state is not None:
            self.state = state
            self.repository = None
        else:
            self.session_ctx = get_session()
            try:
                self.session = next(self.session_ctx)
            except TypeError:
                self.session = self.session_ctx
            self.repository = StateRepository(self.session)
            self.state = self.repository.get_latest_state()

    def process_action(self, action: PlayerAction) -> NarrativeResult:
        # 1. Build prompt using prompt_utils
        prompt_str = build_narrative_prompt(self.state, action)
        
        # 2. Call vllm_client.generate()
        raw_data = self.vllm_client.generate(prompt_str)
        
        # If it's a raw vLLM response containing 'choices', parse the text from choices
        if isinstance(raw_data, dict) and "choices" in raw_data:
            raw_text = raw_data["choices"][0]["text"]
            parsed_data = parse_llm_response(raw_text)
            raw_response = RawResponse(**parsed_data)
        else:
            # If it's already pre-parsed (like in test_engine.py)
            raw_response = RawResponse(**raw_data)
        
        # 3. Parse result
        narration = raw_response.text
        
        # 4. Update state
        state_updates = raw_response.state_updates
        if state_updates:
            if "location_id" in state_updates:
                loc_id = state_updates["location_id"]
                # Update location properties in DB
                self.repository.update_location(loc_id, state_updates)
                # Update active world state's location ID
                self.state.current_location_id = loc_id
                
            if "active_npcs" in state_updates:
                npc_ids = []
                for npc_data in state_updates["active_npcs"]:
                    npc_id = npc_data.get("id")
                    if npc_id:
                        npc_ids.append(npc_id)
                        # Save or update NPC details
                        npc = self.session.exec(select(NPC).where(NPC.id == npc_id)).first()
                        if not npc:
                            npc = NPC(
                                id=npc_id,
                                name=npc_data.get("name", ""),
                                traits=npc_data.get("traits", []),
                                location_id=self.state.current_location_id
                            )
                            self.session.add(npc)
                        else:
                            npc.name = npc_data.get("name", npc.name)
                            npc.traits = npc_data.get("traits", npc.traits)
                            npc.location_id = self.state.current_location_id
                            self.session.add(npc)
                self.state.active_npcs_ids = ",".join(npc_ids)
                
            if "global_event" in state_updates:
                self.state.global_event = state_updates["global_event"]
            if "world_memories" in state_updates:
                self.state.world_memories = state_updates["world_memories"]
            
            # Save the updated state
            self.repository.save_state(self.state)
        
        # 5. Handle Dynamic Events
        events = []
        if raw_response.events:
            events = raw_response.events
            print(f"Dynamic Events Triggered: {events}")

        return NarrativeResult(
            narration=narration,
            state_updates=state_updates,
            active_npcs=[npc.name for npc in self.state.active_npcs],
            events=events
        )
