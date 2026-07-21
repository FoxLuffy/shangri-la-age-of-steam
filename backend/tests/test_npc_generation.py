import pytest
from sqlmodel import Session, select
from backend.main import app
from backend.database import engine as db_engine, get_session
from fastapi.testclient import TestClient

def test_procedural_npc_generation_logic():
    from backend.npc_generator import generate_procedural_npc
    from backend.database import NPC
    
    with Session(db_engine) as session:
        # Generate an NPC for a specific location flavor
        npc = generate_procedural_npc(session, location_flavor="industrial")
        
        assert npc.id is not None
        assert npc.name is not None
        assert len(npc.name) > 0
        assert len(npc.traits) >= 3
        role = npc.traits[0]
        assert "industrial" in role.lower() or "steam" in role.lower() or "factory" in role.lower() or "brass" in role.lower() or "engineer" in role.lower() or "worker" in role.lower() or "machinist" in role.lower() or "foreman" in role.lower() or "shoveler" in role.lower()

def test_api_generate_npc():
    client = TestClient(app)
    response = client.post("/generate_npc?flavor=alchemical")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "traits" in data
    assert len(data["traits"]) > 0
