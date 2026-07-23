import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from backend.models import PlayerAction
from backend.engine import NarrativeEngine
from backend.database import NPC, Location, Item
from backend.repository import StateRepository

@pytest.fixture
def engine_session():
    # Use a temporary in-memory database for testing
    sqlite_url = "sqlite:///:memory:"
    engine = create_engine(sqlite_url, echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

class MockVLLMClient:
    def __init__(self, response_data):
        self.response_data = response_data
        
    def generate_stream(self, prompt, **kwargs):
        yield self.response_data

def test_dynamic_database_ingestion(engine_session):
    # Prepare the mock response containing new_entities
    mock_response = """[Narration]You discover a new area and meet someone strange.
[StateUpdates]
{
    "new_entities": [
        {
            "type": "NPC",
            "id": "new_npc_001",
            "name": "Elias the Strange",
            "traits": ["Mysterious", "Tinkerer"]
        },
        {
            "type": "Location",
            "id": "hidden_workshop",
            "name": "Hidden Workshop",
            "description": "A secret workshop full of gears."
        },
        {
            "type": "Item",
            "name": "Mystic Gear",
            "description": "A gear that hums with energy.",
            "category": "Steam_Tech_Components"
        }
    ]
}"""
    
    # Initialize the narrative engine with the mock client
    mock_client = MockVLLMClient(mock_response)
    engine = NarrativeEngine(vllm_client=mock_client)
    
    action = PlayerAction(
        action_text="look around",
        current_location_id="1",
        character_id=1
    )
    
    # Process the action
    result = list(engine.process_action(action, session=engine_session))
    
    # Verify the new entities are in the database
    npc = engine_session.exec(select(NPC).where(NPC.id == "new_npc_001")).first()
    assert npc is not None
    assert npc.name == "Elias the Strange"
    assert "Mysterious" in npc.traits
    
    loc = engine_session.exec(select(Location).where(Location.id == "hidden_workshop")).first()
    assert loc is not None
    assert loc.name == "Hidden Workshop"
    assert loc.description == "A secret workshop full of gears."
    
    item = engine_session.exec(select(Item).where(Item.name == "Mystic Gear")).first()
    assert item is not None
    assert item.description == "A gear that hums with energy."
    assert item.category == "Steam_Tech_Components"
