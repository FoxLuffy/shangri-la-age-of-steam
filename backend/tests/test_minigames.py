import pytest
from sqlmodel import Session, select
from backend.main import app
from backend.database import engine as db_engine, get_session
from fastapi.testclient import TestClient

def test_gear_lock_minigame():
    from backend.database import Character, Minigame
    with Session(db_engine) as session:
        char = Character(name="Spy")
        session.add(char)
        session.commit()
        
        client = TestClient(app)
        
        # 1. Start minigame
        res1 = client.post(f"/minigames/start?character_id={char.id}&game_type=gear_lock")
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["type"] == "gear_lock"
        assert not data1["solved"]
        game_id = data1["id"]
        
        # 2. Perform an action to solve
        # A gear lock might start with all 0s and need to reach 5s. We'll just mock it or force a win
        # For the test, we'll hit an endpoint that just tries to solve it directly or increments a gear.
        
        res2 = client.post(f"/minigames/{game_id}/action", json={"action": "solve_cheat"})
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["solved"] is True
