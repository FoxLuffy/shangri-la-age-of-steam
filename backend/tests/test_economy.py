import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlmodel import Session, select
import math

from backend.main import app
from backend.database import engine as db_engine, get_session, ResourceMarket, WorldEvent

@pytest.fixture(autouse=True)
def setup_test_db():
    from backend.database import create_db_and_tables
    create_db_and_tables()
    with Session(db_engine) as session:
        # Clear existing
        session.exec(select(ResourceMarket)).all() # clear?
        for _ in session.exec(select(ResourceMarket)).all():
            session.delete(_)
        for _ in session.exec(select(WorldEvent)).all():
            session.delete(_)
        
        # Seed test market
        session.add(ResourceMarket(resource_name="Coal", base_price=10.0, current_price=10.0, volatility=0.1))
        session.add(ResourceMarket(resource_name="Brass", base_price=25.0, current_price=25.0, volatility=0.2))
        session.add(ResourceMarket(resource_name="Aether", base_price=100.0, current_price=100.0, volatility=0.5))
        session.commit()
    yield

def test_get_market_prices():
    client = TestClient(app)
    response = client.get("/market")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["resource_name"] == "Coal"
    assert data[0]["current_price"] == 10.0

def test_economy_tick_fluctuates_prices():
    from backend.engine import simulate_economy_tick
    with Session(db_engine) as session:
        # Add an event that affects Coal
        event = WorldEvent(
            location_id="1", 
            event_type="mining_strike", 
            event_text="Miners are on strike!",
            severity=3,
            faction_impacts={"Coal": 2.0}  # Modifier for Coal price
        )
        session.add(event)
        session.commit()
        
        simulate_economy_tick(session)
        
        coal = session.exec(select(ResourceMarket).where(ResourceMarket.resource_name == "Coal")).first()
        assert coal is not None
        # Price should increase due to the strike event modifier (severity 3 * impact 2.0)
        assert coal.current_price > 10.0
