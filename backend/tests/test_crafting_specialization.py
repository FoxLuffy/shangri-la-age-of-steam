from backend.database import (
    Character,
    CraftingProficiency,
    Inventory,
    Item,
    ItemCategory,
    Location,
    Recipe,
    RecipeRequirement,
    SQLModel,
    WorldState,
    engine,
)
from backend.main import app
from backend.routers.crafting import level_for_xp
from fastapi.testclient import TestClient
from sqlmodel import Session, select

client = TestClient(app)


def setup_db(branch="metallurgy", tier=0):
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        char = Character(name="Smith")
        session.add(char)
        session.add(Location(id="1", name="Forge", description="", faction_id=None))
        session.add(WorldState(current_location_id="1"))

        ore = Item(name="Ore", category=ItemCategory.crafting_materials)
        blade = Item(name="Blade", category=ItemCategory.equipment)
        session.add(ore)
        session.add(blade)
        session.commit()
        session.refresh(char)
        session.refresh(ore)
        session.refresh(blade)

        recipe = Recipe(name="Forge Blade", result_item_id=blade.id, branch=branch, tier=tier)
        session.add(recipe)
        session.commit()
        session.refresh(recipe)
        session.add(RecipeRequirement(recipe_id=recipe.id, item_id=ore.id, quantity=1))
        session.add(Inventory(character_id=char.id, item_id=ore.id, quantity=10))
        session.commit()

        return {"character_id": char.id, "recipe_id": recipe.id, "ore_id": ore.id, "blade_id": blade.id}


def _discover(cid, rid):
    client.post("/crafting/discover", json={"character_id": cid, "recipe_id": rid})


def _set_xp(character_id, branch, xp):
    with Session(engine) as session:
        prof = CraftingProficiency(character_id=character_id, branch=branch, xp=xp)
        session.add(prof)
        session.commit()


def _ore_count(character_id, ore_id):
    with Session(engine) as session:
        inv = session.exec(
            select(Inventory).where(Inventory.character_id == character_id, Inventory.item_id == ore_id)
        ).first()
        return inv.quantity if inv else 0


def test_level_for_xp_caps_at_10():
    assert level_for_xp(0) == 0
    assert level_for_xp(3) == 1
    assert level_for_xp(8) == 2
    assert level_for_xp(999) == 10


def test_proficiency_endpoint_initializes_all_branches():
    ids = setup_db()
    resp = client.get(f"/crafting/proficiency?character_id={ids['character_id']}")
    assert resp.status_code == 200
    data = {p["branch"]: p for p in resp.json()}
    assert set(data) == {"metallurgy", "alchemy", "clockwork"}
    assert all(p["level"] == 0 and p["xp"] == 0 for p in data.values())


def test_tier_gate_blocks_when_underleveled():
    ids = setup_db(branch="metallurgy", tier=3)
    cid, rid = ids["character_id"], ids["recipe_id"]
    _discover(cid, rid)

    resp = client.post(f"/craft?character_id={cid}&recipe_id={rid}")
    assert resp.status_code == 400
    assert "proficiency" in resp.json()["detail"].lower()


def test_success_crafts_and_grants_xp(monkeypatch):
    ids = setup_db(branch="metallurgy", tier=0)
    cid, rid = ids["character_id"], ids["recipe_id"]
    _discover(cid, rid)
    monkeypatch.setattr("backend.routers.crafting.roll_success", lambda chance: True)

    resp = client.post(f"/craft?character_id={cid}&recipe_id={rid}")
    assert resp.status_code == 200
    assert resp.json()["crafted"] is True

    prof = {p["branch"]: p for p in client.get(f"/crafting/proficiency?character_id={cid}").json()}
    assert prof["metallurgy"]["xp"] == 1


def test_failure_consumes_materials_without_result(monkeypatch):
    ids = setup_db(branch="metallurgy", tier=0)
    cid, rid, ore_id, blade_id = ids["character_id"], ids["recipe_id"], ids["ore_id"], ids["blade_id"]
    _discover(cid, rid)
    monkeypatch.setattr("backend.routers.crafting.roll_success", lambda chance: False)

    resp = client.post(f"/craft?character_id={cid}&recipe_id={rid}")
    assert resp.status_code == 200
    assert resp.json()["crafted"] is False

    # Ore consumed (10 -> 9), no blade produced, no XP.
    assert _ore_count(cid, ore_id) == 9
    with Session(engine) as session:
        blade_inv = session.exec(
            select(Inventory).where(Inventory.character_id == cid, Inventory.item_id == blade_id)
        ).first()
        assert blade_inv is None
    prof = {p["branch"]: p for p in client.get(f"/crafting/proficiency?character_id={cid}").json()}
    assert prof["metallurgy"]["xp"] == 0


def test_nonbranch_recipe_is_deterministic(monkeypatch):
    ids = setup_db(branch=None, tier=0)
    cid, rid = ids["character_id"], ids["recipe_id"]
    _discover(cid, rid)
    # Even if the roll would fail, a branchless recipe always succeeds.
    monkeypatch.setattr("backend.routers.crafting.roll_success", lambda chance: False)

    resp = client.post(f"/craft?character_id={cid}&recipe_id={rid}")
    assert resp.status_code == 200
    assert resp.json().get("crafted", True) is True
