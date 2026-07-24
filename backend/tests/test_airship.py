from backend.database import Character
from backend.database import engine as db_engine
from backend.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session


def test_airship_mechanics():
    with Session(db_engine) as session:
        char = Character(name="Captain")
        session.add(char)
        session.commit()
        session.refresh(char)

        client = TestClient(app)

        # 1. Acquire Airship
        res1 = client.post(f"/airships/acquire?character_id={char.id}&name=The%20Iron%20Zeppelin")
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["name"] == "The Iron Zeppelin"
        assert data1["fuel_level"] == 100.0
        airship_id = data1["id"]

        # 2. Install Module
        res2 = client.post(f"/airships/{airship_id}/install_module?module_name=Aether%20Engine")
        assert res2.status_code == 200
        assert "Aether Engine" in res2.json()["modules"]

        # 3. Fly (consume fuel and change altitude)
        res3 = client.post(f"/airships/{airship_id}/fly?altitude=5000&distance=10")
        assert res3.status_code == 200
        data3 = res3.json()
        assert data3["current_altitude"] == 5000
        assert data3["fuel_level"] < 100.0
