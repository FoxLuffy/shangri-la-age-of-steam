import io
import json
import os

from backend.database import NPC as DBNPC
from backend.database import Faction, Item, Location, SQLModel, engine
from backend.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session, select

client = TestClient(app)

EXAMPLE_MOD = os.path.join(
    os.path.dirname(__file__), "..", "..", "docs", "mods", "example_mod.json"
)


def test_example_mod_uploads_and_creates_entities():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with open(EXAMPLE_MOD, "rb") as f:
        raw = f.read()

    # The template must be valid JSON.
    data = json.loads(raw)

    resp = client.post(
        "/modding/upload",
        files={"file": ("example_mod.json", io.BytesIO(raw), "application/json")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "success"

    with Session(engine) as session:
        faction = session.get(Faction, data["factions"][0]["id"])
        assert faction is not None and faction.name == "The Clockwork Cabal"

        location = session.get(Location, data["locations"][0]["id"])
        assert location is not None and location.faction_id == faction.id

        npc = session.get(DBNPC, data["npcs"][0]["id"])
        assert npc is not None and npc.location_id == location.id

        item = session.exec(select(Item).where(Item.name == data["items"][0]["name"])).first()
        assert item is not None and item.category == "Steam_Tech_Components"
