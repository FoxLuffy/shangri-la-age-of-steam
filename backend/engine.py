from backend.models import WorldState, PlayerAction, NarrativeResult, Prompt, RawResponse
from backend.client import VLLMClient
from backend.prompt_utils import build_narrative_prompt
from backend.repository import StateRepository
import json
from typing import Any
from sqlalchemy.orm import Session as SQLModelSession
from backend.database import get_session

class NarrativeEngine:
    def __init__(self, vllm_client: VLLMClient):
        self.vllm_client = vllm_client
        self.session_factory = get_session
        self.repository = StateRepository(self.session_factory())
        self.state = self.repository.get_latest_state()

    def process_action(self, action: PlayerAction) -> NarrativeResult:
        # 1. Build prompt using prompt_utils
        prompt_str = build_narrative_prompt(self.state, action)
        
        # Inject Mood and Exploration instructions
        if action.mood:
            prompt_str += f"\n\n[Mood: {action.mood}]"
            
        if action.is_exploration:
            prompt_str += "\n\nProvide a detailed description of the surroundings."
        
        # 2. Call vllm_client.generate()
        raw_data = self.vllm_client.generate(prompt_str)
        raw_response = RawResponse(**raw_data)
        
        # 3. Parse result
        narration = raw_response.text
        
        # 4. Update state
        state_updates = raw_response.state_updates
        if state_updates:
            if "location_id" in state_updates:
                self.repository.update_location(state_updates["location_id"], state_updates)
            
            # Save the updated state
            self.repository.save_state(self.state)
        
        # 5. Handle Dynamic Events
        events = []
        if raw_response.events:
            events = raw_response.events
            # Simple implementation: just log events for now
            # Future: logic to process 'effects' and update state
            print(f"Dynamic Events Triggered: {events}")

        return NarrativeResult(
            narration=narration,
            state_updates=state_updates,
            active_npcs=[npc.name for npc in self.state.active_npcs],
            events=events
        )
