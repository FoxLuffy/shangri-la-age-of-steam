from backend.models import WorldState, PlayerAction, NarrativeResult, Prompt, RawResponse
from backend.client import VLLMClient
from backend.prompt_utils import build_narrative_prompt
from backend.repository import StateRepository
import json
from typing import Any
from sqlalchemy.orm import Session
from backend.database import get_session

class NarrativeEngine:
    def __init__(self, vllm_client: VLLMClient):
        self.vllm_client = vllm_client

    def process_action(self, action: PlayerAction, session: Session) -> NarrativeResult:
        # Use the repository with the provided session
        repository = StateRepository(session)
        
        # 1. Get the latest state
        state = repository.get_latest_state()
        
        # 2. Build prompt using prompt_utils
        prompt_str = build_narrative_prompt(state, action)
        
        # Inject Mood and Exploration instructions
        if hasattr(action, 'mood') and action.mood:
            prompt_str += f"\n\n[Mood: {action.mood}]"
            
        if hasattr(action, 'is_exploration') and action.is_exploration:
            prompt_str += "\n\nProvide a detailed description of the surroundings."
        
        # 3. Call vllm_client.generate()
        raw_data = self.vllm_client.generate(prompt_str)
        raw_response = RawResponse(**raw_data)
        
        # 4. Parse result
        narration = raw_response.text
        
        # 5. Update state
        state_updates = raw_response.state_updates
        if state_updates:
            if "location_id" in state_updates:
                repository.update_location(state_updates["location_id"], state_updates)
            
            # Save the updated state
            repository.save_state(state)
        
        # 6. Handle Dynamic Events
        events = []
        if raw_response.events:
            events = raw_response.events
            # Simple implementation: just log events for now
            # Future: logic to process 'effects' and update state
            print(f"Dynamic Events Triggered: {events}")
        
        return NarrativeResult(
            narration=narration,
            state_updates=state_updates,
            npcs=[npc.name for npc in state.active_npcs] if hasattr(state, 'active_npcs') else [],
            events=events
        )
