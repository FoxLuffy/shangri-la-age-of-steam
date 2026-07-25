from backend.database import (
    Character,
    Inventory,
    Item,
    ItemCategory,
    Quest,
    QuestState,
    QuestStateEnum,
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


def test_load_restores_character_world_inventory_quests():
    ids = setup_db()
    cid = ids["character_id"]
    save_id = client.post("/saves", json={"character_id": cid}).json()["id"]

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

    resp = client.get(f"/saves/{save_id}/load")
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


def test_load_unknown_save_404():
    setup_db()
    resp = client.get("/saves/424242/load")
    assert resp.status_code == 404


def test_list_saves_for_character():
    ids = setup_db()
    cid = ids["character_id"]
    client.post("/saves", json={"character_id": cid, "name": "slot A"})
    client.post("/saves", json={"character_id": cid, "name": "slot B"})

    resp = client.get(f"/saves?character_id={cid}")
    assert resp.status_code == 200
    saves = resp.json()
    assert len(saves) == 2
    names = {s["name"] for s in saves}
    assert names == {"slot A", "slot B"}


def test_delete_save():
    ids = setup_db()
    cid = ids["character_id"]
    save_id = client.post("/saves", json={"character_id": cid}).json()["id"]

    resp = client.delete(f"/saves/{save_id}")
    assert resp.status_code == 200

    # Gone: loading it now 404s.
    assert client.get(f"/saves/{save_id}/load").status_code == 404
    assert client.get(f"/saves?character_id={cid}").json() == []
