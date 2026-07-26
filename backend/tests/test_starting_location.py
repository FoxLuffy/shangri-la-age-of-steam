"""CR9: new characters shouldn't always start in the same location."""

from backend.database import Character, Location, SQLModel, User, engine
from backend.database_init import seed_demo_user
from backend.main import app, pick_starting_location
from fastapi.testclient import TestClient
from sqlmodel import Session, select

client = TestClient(app)


def _seed_locations():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for i in range(1, 6):
            session.add(Location(id=str(i), name=f"Loc {i}", description=""))
        session.commit()


def test_origin_maps_to_thematic_location():
    _seed_locations()
    with Session(engine) as session:
        assert pick_starting_location(session, "Smuggler's Ward") == "5"
        assert pick_starting_location(session, "Aristocratic Heir") == "2"


def test_unknown_origin_returns_an_existing_location():
    _seed_locations()
    with Session(engine) as session:
        loc = pick_starting_location(session, "Wanderer of Nowhere")
        assert loc in {"1", "2", "3", "4", "5"}


def test_no_locations_defaults_to_1():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        assert pick_starting_location(session, "Foundry Orphan") == "1"


def test_create_character_uses_origin_location():
    _seed_locations()
    seed_demo_user()
    with Session(engine) as session:
        uid = session.exec(select(User).where(User.username == "demo")).first().id
    resp = client.post("/characters", json={
        "name": "Sly", "preset": "Scrapper", "origin": "Smuggler's Ward",
        "backstory": "", "gear": [], "user_id": uid,
    })
    assert resp.status_code == 200
    cid = resp.json()["id"]
    with Session(engine) as session:
        assert session.get(Character, cid).location_id == "5"
