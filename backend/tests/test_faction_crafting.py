from backend.database import engine as db_engine
from backend.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session, select


def test_faction_crafting():
    from backend.database import (
        Character,
        Inventory,
        Item,
        ItemCategory,
        Location,
        Recipe,
        RecipeRequirement,
        WorldState,
    )

    with Session(db_engine) as session:
        char = Character(name="Crafter")
        session.add(char)
        session.commit()

        loc_alchemist = Location(id="loc_alc", name="Alchemist Lab", description="", faction_id="alchemists")
        loc_other = Location(id="loc_oth", name="Street", description="", faction_id="none")
        session.add(loc_alchemist)
        session.add(loc_other)

        ws = session.exec(select(WorldState)).first()
        if not ws:
            ws = WorldState(current_location_id="loc_alc")
            session.add(ws)
        else:
            ws.current_location_id = "loc_alc"
            session.add(ws)

        item_in = Item(name="Base Potion", category=ItemCategory.consumables)
        item_out = Item(name="Advanced Potion", category=ItemCategory.consumables)
        session.add(item_in)
        session.add(item_out)
        session.commit()

        inv = Inventory(character_id=char.id, item_id=item_in.id, quantity=5)
        session.add(inv)

        recipe = Recipe(name="Brew Advanced", result_item_id=item_out.id, required_faction_id="alchemists")
        session.add(recipe)
        session.commit()
        session.refresh(recipe)

        req = RecipeRequirement(recipe_id=recipe.id, item_id=item_in.id, quantity=1)
        session.add(req)
        session.commit()

        # Test API
        client = TestClient(app)

        # 1. Success in alchemist location
        res1 = client.post(f"/craft?character_id={char.id}&recipe_id={recipe.id}")
        if res1.status_code != 200:
            print(res1.json())
        assert res1.status_code == 200

        # 2. Failure in other location
        ws.current_location_id = "loc_oth"
        session.add(ws)
        session.commit()

        res2 = client.post(f"/craft?character_id={char.id}&recipe_id={recipe.id}")
        assert res2.status_code == 400
        assert "faction" in res2.json()["detail"].lower()
