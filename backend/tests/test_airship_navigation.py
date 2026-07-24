import random

from backend.database import Airship, Character
from backend.database import engine as db_engine
from backend.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session


def test_airship_navigate():
    with Session(db_engine) as session:
        char = Character(name="Navigator", location_id="start_port")
        session.add(char)
        session.commit()
        session.refresh(char)

        ship = Airship(name="Cloud Strider", character_id=char.id, fuel_level=100.0, hull_integrity=100.0)
        session.add(ship)
        session.commit()
        session.refresh(ship)

        client = TestClient(app)

        # Ensure no encounter
        random.seed(42)  # random.random() -> 0.6394267984578837

        req_data = {"character_id": char.id, "location_id": "sky_port"}
        res = client.post("/gameplay/airships/navigate", json=req_data)
        assert res.status_code == 200
        data = res.json()

        assert data["ship"]["fuel_level"] == 85.0
        assert data["character"]["location_id"] == "sky_port"
        assert data["ship"]["hull_integrity"] == 100.0
        assert "successfully navigated" in data["narration"]

        # Ensure encounter
        random.seed(1)  # random.random() -> 0.13436424411240122

        req_data2 = {"character_id": char.id, "location_id": "aether_city"}
        res2 = client.post("/gameplay/airships/navigate", json=req_data2)
        assert res2.status_code == 200
        data2 = res2.json()

        assert data2["ship"]["fuel_level"] == 70.0
        assert data2["character"]["location_id"] == "aether_city"
        assert data2["ship"]["hull_integrity"] == 90.0
        assert "encountered heavy aether storms" in data2["narration"]
