import pytest
from sqlmodel import Session, SQLModel, create_engine
from unittest.mock import MagicMock
from backend.engine import NarrativeEngine
from backend.models import PlayerAction
from backend.database import Location, NPC, WorldState
from backend.client import VLLMClient

def test_narrative_engine_vllm_call():
    engine_db = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine_db)
    
    with Session(engine_db) as session:
        loc = Location(id="1", name="Forest", description="Forest", npcs=[])
        state = WorldState(current_location_id="1", active_npcs_ids=[])
        session.add(loc)
        session.add(state)
        session.commit()
        
        # Mock the client
        mock_client = MagicMock(spec=VLLMClient)
        mock_client.generate.return_value = {
            "text": "The trees rustle.",
            "state_updates": {},
            "events": []
        }
        
        engine = NarrativeEngine(vllm_client=mock_client)
        action = PlayerAction(action_text="Look around", current_location_id="1")
        
        result = engine.process_action(action, session)
        assert "trees rustle" in result.narration.lower()
