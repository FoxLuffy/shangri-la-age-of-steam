"""apply_inventory_update: add and remove must affect the character's actual inventory,
even when a duplicate Item row shares the same name (which made removes no-op)."""

from backend.database import Character, Inventory, Item, ItemCategory, SQLModel, engine
from backend.repository import StateRepository
from sqlmodel import Session, select


def _qty(session, cid, name):
    total = 0
    for inv in session.exec(select(Inventory).where(Inventory.character_id == cid)).all():
        it = session.get(Item, inv.item_id)
        if it and it.name == name:
            total += inv.quantity
    return total


def test_remove_decrements_the_characters_item_despite_duplicate_item_rows():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        char = Character(name="Tinker")
        session.add(char)
        # Two Item rows share the name "Scrap Metal"; the character holds the SECOND one.
        session.add(Item(name="Scrap Metal", category=ItemCategory.crafting_materials))  # id 1 (not held)
        held = Item(name="Scrap Metal", category=ItemCategory.crafting_materials)         # id 2 (held)
        session.add(held)
        session.commit()
        session.refresh(char)
        session.refresh(held)
        session.add(Inventory(character_id=char.id, item_id=held.id, quantity=1))
        session.commit()
        cid = char.id

    with Session(engine) as session:
        repo = StateRepository(session)
        repo.apply_inventory_update({"action": "remove", "item_name": "Scrap Metal", "quantity": 1}, cid)
        assert _qty(session, cid, "Scrap Metal") == 0  # actually removed


def test_add_then_remove_roundtrip():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        char = Character(name="Tinker")
        session.add(char)
        session.commit()
        session.refresh(char)
        cid = char.id
    with Session(engine) as session:
        repo = StateRepository(session)
        repo.apply_inventory_update({"action": "add", "item_name": "Crude Lockpick", "quantity": 2}, cid)
        assert _qty(session, cid, "Crude Lockpick") == 2
        repo.apply_inventory_update({"action": "remove", "item_name": "Crude Lockpick", "quantity": 1}, cid)
        assert _qty(session, cid, "Crude Lockpick") == 1
