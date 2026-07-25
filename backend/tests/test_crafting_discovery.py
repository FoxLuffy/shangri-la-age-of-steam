from backend.database import (
    Character,
    Inventory,
    Item,
    ItemCategory,
    KnownRecipe,
    Location,
    Recipe,
    RecipeRequirement,
    SQLModel,
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
        char = Character(name="Tinkerer")
        session.add(char)

        loc = Location(id="1", name="Workshop", description="", faction_id=None)
        session.add(loc)
        session.add(WorldState(current_location_id="1"))

        cog = Item(name="Cog", category=ItemCategory.crafting_materials)
        spring = Item(name="Spring", category=ItemCategory.crafting_materials)
        gadget = Item(name="Gadget", category=ItemCategory.equipment)
        session.add(cog)
        session.add(spring)
        session.add(gadget)
        session.commit()
        session.refresh(char)
        session.refresh(cog)
        session.refresh(spring)
        session.refresh(gadget)

        recipe = Recipe(name="Assemble Gadget", result_item_id=gadget.id, result_quantity=1)
        session.add(recipe)
        session.commit()
        session.refresh(recipe)
        session.add(RecipeRequirement(recipe_id=recipe.id, item_id=cog.id, quantity=2))
        session.add(RecipeRequirement(recipe_id=recipe.id, item_id=spring.id, quantity=1))

        # Materials for crafting + experimentation.
        session.add(Inventory(character_id=char.id, item_id=cog.id, quantity=5))
        session.add(Inventory(character_id=char.id, item_id=spring.id, quantity=5))
        session.commit()

        return {
            "character_id": char.id,
            "recipe_id": recipe.id,
            "cog_id": cog.id,
            "spring_id": spring.id,
            "gadget_id": gadget.id,
        }


def _known_ids(character_id):
    with Session(engine) as session:
        return [
            k.recipe_id
            for k in session.exec(select(KnownRecipe).where(KnownRecipe.character_id == character_id)).all()
        ]


def test_discover_grants_recipe_and_is_idempotent():
    ids = setup_db()
    cid, rid = ids["character_id"], ids["recipe_id"]

    resp = client.post("/crafting/discover", json={"character_id": cid, "recipe_id": rid, "method": "dialogue"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "discovered"
    assert _known_ids(cid) == [rid]

    # Second call: idempotent, no duplicate row.
    resp2 = client.post("/crafting/discover", json={"character_id": cid, "recipe_id": rid})
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "already_known"
    assert _known_ids(cid) == [rid]


def test_discover_unknown_character_or_recipe_404():
    ids = setup_db()
    assert client.post("/crafting/discover", json={"character_id": 999, "recipe_id": ids["recipe_id"]}).status_code == 404
    assert client.post("/crafting/discover", json={"character_id": ids["character_id"], "recipe_id": 999}).status_code == 404


def test_known_lists_discovered_recipes():
    ids = setup_db()
    cid, rid = ids["character_id"], ids["recipe_id"]
    client.post("/crafting/discover", json={"character_id": cid, "recipe_id": rid, "method": "purchase"})

    resp = client.get(f"/crafting/known?character_id={cid}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["recipe_id"] == rid
    assert data[0]["name"] == "Assemble Gadget"
    assert data[0]["method"] == "purchase"


def test_known_includes_requirements_and_result_name():
    ids = setup_db()
    cid, rid = ids["character_id"], ids["recipe_id"]
    client.post("/crafting/discover", json={"character_id": cid, "recipe_id": rid})

    row = client.get(f"/crafting/known?character_id={cid}").json()[0]
    assert row["result_name"] == "Gadget"
    assert "branch" in row and "tier" in row
    req_names = {r["name"]: r["quantity"] for r in row["requirements"]}
    assert req_names == {"Cog": 2, "Spring": 1}


def test_materials_endpoint_lists_owned_items_with_names():
    ids = setup_db()
    cid = ids["character_id"]
    mats = {m["name"]: m["quantity"] for m in client.get(f"/crafting/materials?character_id={cid}").json()}
    assert mats == {"Cog": 5, "Spring": 5}


def test_experiment_discovers_matching_recipe_on_success(monkeypatch):
    ids = setup_db()
    cid = ids["character_id"]
    monkeypatch.setattr("backend.routers.crafting.random.random", lambda: 0.0)  # force success

    resp = client.post(
        "/crafting/experiment",
        json={"character_id": cid, "item_ids": [ids["cog_id"], ids["spring_id"]]},
    )
    assert resp.status_code == 200
    discovered = resp.json()["discovered"]
    assert discovered is not None
    assert discovered["recipe_id"] == ids["recipe_id"]
    assert _known_ids(cid) == [ids["recipe_id"]]


def test_experiment_no_match_returns_null(monkeypatch):
    ids = setup_db()
    cid = ids["character_id"]
    monkeypatch.setattr("backend.routers.crafting.random.random", lambda: 0.0)

    # Only cog provided; recipe also needs a spring → no fully-satisfiable recipe.
    resp = client.post("/crafting/experiment", json={"character_id": cid, "item_ids": [ids["cog_id"]]})
    assert resp.status_code == 200
    assert resp.json()["discovered"] is None
    assert _known_ids(cid) == []


def test_experiment_skips_already_known(monkeypatch):
    ids = setup_db()
    cid = ids["character_id"]
    client.post("/crafting/discover", json={"character_id": cid, "recipe_id": ids["recipe_id"]})
    monkeypatch.setattr("backend.routers.crafting.random.random", lambda: 0.0)

    resp = client.post(
        "/crafting/experiment",
        json={"character_id": cid, "item_ids": [ids["cog_id"], ids["spring_id"]]},
    )
    assert resp.json()["discovered"] is None


def test_craft_gated_on_discovery():
    ids = setup_db()
    cid, rid = ids["character_id"], ids["recipe_id"]

    # Not discovered yet → forbidden.
    blocked = client.post(f"/craft?character_id={cid}&recipe_id={rid}")
    assert blocked.status_code == 403

    # Discover, then craft succeeds.
    client.post("/crafting/discover", json={"character_id": cid, "recipe_id": rid})
    ok = client.post(f"/craft?character_id={cid}&recipe_id={rid}")
    assert ok.status_code == 200
