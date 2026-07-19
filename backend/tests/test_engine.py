import pytest
from sqlmodel import Session, SQLModel, create_engine
from backend.engine import NarrativeEngine
from backend.models import PlayerAction
from backend.database import Location, NPC, WorldState
from unittest.mock import MagicMock

def test_narrative_engine_processing():
    # Setup in-memory DB for tests
    engine_db = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine_db)
    
    with Session(engine_db) as session:
        # Seed test data using DB models
        loc = Location(id="1", name="Forest", description="A dark forest", npcs=["Orc"])
        npc = NPC(id="1", name="Orc", traits=["strong", "aggressive"], location_id="1")
        state = WorldState(current_location_id="1", active_npcs_ids=["1"])
        
        session.add(loc)
        session.add(npc)
        session.add(state)
        session.commit()
        
        # Mock VLLMClient
        mock_vllm_client = MagicMock()
        mock_vllm_client.generate.return_value = {
            "text": "You enter the dark forest, encountering an Orc.",
            "state_updates": {},
            "events": []
        }
        
        # Initialize engine
        engine = NarrativeEngine(mock_vllm_client)
        action = PlayerAction(action_text="I walk into the forest", current_location_id="1")
        
        result = engine.process_action(action, session)
        assert "forest" in result.narration.lower()
