from backend.database import engine as db_engine
from backend.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session


def test_character_creation_preset():
    from backend.database import Character

    with Session(db_engine) as session:
        char = Character(
            name="Percival",
            character_class="Aristocrat",
            background="Wealthy heir to a steam-engine fortune.",
            stats={"strength": 3, "intellect": 7, "charm": 8},
        )
        session.add(char)
        session.commit()
        session.refresh(char)

        assert char.id is not None
        assert char.name == "Percival"
        assert char.character_class == "Aristocrat"
        assert char.stats["charm"] == 8


def test_api_create_character():
    client = TestClient(app)
    response = client.post("/characters", json={"name": "Lyra", "preset": "Scrapper"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Lyra"
    assert data["character_class"] == "Scrapper"
    assert "stats" in data
    assert data["stats"]["strength"] >= 5  # Scrappers are strong


def test_api_create_character_origin():
    from backend.database import NPC, Inventory, Item
    from backend.database import engine as db_engine
    from sqlmodel import Session, select

    client = TestClient(app)
    response = client.post("/characters", json={"name": "Lyra Origin", "preset": "Scrapper", "origin": "Foundry Orphan"})
    assert response.status_code == 200
    data = response.json()
    char_id = data["id"]

    with Session(db_engine) as session:
        # Check that the items were created and added to inventory
        inv_items = session.exec(select(Inventory).where(Inventory.character_id == char_id)).all()
        assert len(inv_items) >= 2
        item_names = [session.get(Item, i.item_id).name for i in inv_items]
        assert "Soot-Stained Rag" in item_names
        assert "Scrap Metal" in item_names

        # Check NPC disposition bump
        npc = session.exec(select(NPC).where(NPC.name == "Foreman Ironfist")).first()
        assert npc is not None
        assert npc.disposition >= 0.3
