import pytest
from sqlmodel import Session, select
from backend.main import app
from backend.database import engine as db_engine, get_session
from fastapi.testclient import TestClient

def test_create_and_fetch_automata():
    from backend.database import AutomataCompanion
    with Session(db_engine) as session:
        # Create a clockwork owl
        owl = AutomataCompanion(
            name="Clockwork Owl",
            model_type="scout",
            core_power=100.0,
            modules=["optical_lens", "brass_wings"]
        )
        session.add(owl)
        session.commit()
        session.refresh(owl)

        assert owl.id is not None
        assert owl.name == "Clockwork Owl"
        assert owl.model_type == "scout"
        assert "optical_lens" in owl.modules

def test_api_get_automata():
    from backend.database import AutomataCompanion
    with Session(db_engine) as session:
        hound = AutomataCompanion(
            name="Brass Hound",
            model_type="combat",
            core_power=150.0,
            modules=["pneumatic_jaw", "reinforced_chassis"]
        )
        session.add(hound)
        session.commit()
    
    client = TestClient(app)
    response = client.get("/automata")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 1
    names = [a["name"] for a in data]
    assert "Brass Hound" in names

def test_worldstate_can_have_active_automata():
    from backend.database import WorldState, AutomataCompanion
    with Session(db_engine) as session:
        owl = AutomataCompanion(
            name="Clockwork Owl",
            model_type="scout",
            core_power=100.0,
            modules=[]
        )
        session.add(owl)
        session.commit()
        session.refresh(owl)
        
        ws = session.exec(select(WorldState)).first()
        if not ws:
            ws = WorldState(current_location_id="1")
            session.add(ws)
        
        # Link automata to world state
        ws.active_automata_ids = [owl.id]
        session.add(ws)
        session.commit()
        session.refresh(ws)
        
        assert owl.id in ws.active_automata_ids
