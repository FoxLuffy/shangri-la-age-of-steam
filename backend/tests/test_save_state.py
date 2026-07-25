from backend.database import (
    Character,
    Inventory,
    Item,
    ItemCategory,
    Quest,
    QuestState,
    QuestStateEnum,
    SaveState,
    SQLModel,
    User,
    WorldState,
    engine,
)
from backend.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session, select

client = TestClient(app)


def setup_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(username="saver", password_hash="hash")
        session.add(user)
        session.commit()
        session.refresh(user)

        char = Character(
            user_id=user.id,
            name="Snapshot Hero",
            character_class="Wanderer",
            brass_coins=500,
            hp=90,
            location_id="2",
        )
        session.add(char)

        world = WorldState(current_location_id="2", world_time=42, weather="Fog", time_period="Dusk")
        session.add(world)

        item = Item(name="Brass Cog", description="a cog", category=ItemCategory.crafting_materials)
        session.add(item)

        quest = Quest(title="Find the Cog")
        session.add(quest)
        session.commit()
        session.refresh(char)
        session.refresh(item)
        session.refresh(quest)

        session.add(Inventory(character_id=char.id, item_id=item.id, quantity=3, durability=80))
        session.add(QuestState(character_id=char.id, quest_id=quest.id, state=QuestStateEnum.active))
        session.commit()

        return {"user_id": user.id, "character_id": char.id, "item_id": item.id, "quest_id": quest.id}


def test_create_save_returns_metadata():
    ids = setup_db()
    resp = client.post("/saves", json={"character_id": ids["character_id"], "name": "Before the vault"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["character_id"] == ids["character_id"]
    assert data["name"] == "Before the vault"
    assert "id" in data
    assert data["created_at"]


def test_create_save_unknown_character_404():
    setup_db()
    resp = client.post("/saves", json={"character_id": 999999, "name": "nope"})
    assert resp.status_code == 404


def test_second_save_overwrites_single_slot():
    ids = setup_db()
    cid = ids["character_id"]

    first = client.post("/saves", json={"character_id": cid, "name": "manual"}).json()

    # Change state, then save again (e.g. autosave) — must overwrite the same row.
    with Session(engine) as session:
        char = session.get(Character, cid)
        char.brass_coins = 12345
        session.add(char)
        session.commit()

    second = client.post("/saves", json={"character_id": cid}).json()

    # Same slot (same id), name preserved when not re-specified.
    assert second["id"] == first["id"]
    assert second["name"] == "manual"

    # Exactly one save row exists for this character.
    with Session(engine) as session:
        rows = session.exec(select(SaveState).where(SaveState.character_id == cid)).all()
        assert len(rows) == 1
        assert rows[0].snapshot["character"]["brass_coins"] == 12345


def test_get_save_metadata():
    ids = setup_db()
    cid = ids["character_id"]
    client.post("/saves", json={"character_id": cid, "name": "slot"})

    resp = client.get(f"/saves/{cid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "slot"


def test_get_save_none_404():
    ids = setup_db()
    resp = client.get(f"/saves/{ids['character_id']}")
    assert resp.status_code == 404


def test_load_restores_character_world_inventory_quests():
    ids = setup_db()
    cid = ids["character_id"]
    client.post("/saves", json={"character_id": cid})

    # Mutate everything after the save.
    with Session(engine) as session:
        char = session.get(Character, cid)
        char.brass_coins = 0
        char.hp = 5
        char.location_id = "1"
        session.add(char)

        world = session.exec(select(WorldState)).first()
        world.world_time = 999
        world.weather = "Aether Storm"
        session.add(world)

        inv = session.exec(select(Inventory).where(Inventory.character_id == cid)).first()
        inv.quantity = 0
        session.add(inv)

        qs = session.exec(select(QuestState).where(QuestState.character_id == cid)).first()
        qs.state = QuestStateEnum.failed
        session.add(qs)
        session.commit()

    resp = client.get(f"/saves/{cid}/load")
    assert resp.status_code == 200

    with Session(engine) as session:
        char = session.get(Character, cid)
        assert char.brass_coins == 500
        assert char.hp == 90
        assert char.location_id == "2"

        world = session.exec(select(WorldState)).first()
        assert world.world_time == 42
        assert world.weather == "Fog"

        inv = session.exec(select(Inventory).where(Inventory.character_id == cid)).all()
        assert len(inv) == 1
        assert inv[0].quantity == 3
        assert inv[0].durability == 80

        qs = session.exec(select(QuestState).where(QuestState.character_id == cid)).all()
        assert len(qs) == 1
        assert qs[0].state == QuestStateEnum.active


def test_load_no_save_404():
    ids = setup_db()
    resp = client.get(f"/saves/{ids['character_id']}/load")
    assert resp.status_code == 404


def test_delete_save():
    ids = setup_db()
    cid = ids["character_id"]
    client.post("/saves", json={"character_id": cid})

    resp = client.delete(f"/saves/{cid}")
    assert resp.status_code == 200

    # Gone: fetching/loading now 404s.
    assert client.get(f"/saves/{cid}").status_code == 404
    assert client.get(f"/saves/{cid}/load").status_code == 404
    assert client.delete(f"/saves/{cid}").status_code == 404
