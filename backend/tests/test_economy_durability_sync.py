import pytest
from sqlmodel import Session, select
from backend.database import engine as db_engine, Character, Inventory, Item
from backend.repository import StateRepository

@pytest.fixture(autouse=True)
def setup_test_db():
    from backend.database import create_db_and_tables
    create_db_and_tables()
    with Session(db_engine) as session:
        # Clear specific tables
        for _ in session.exec(select(Inventory)).all():
            session.delete(_)
        for _ in session.exec(select(Item)).all():
            session.delete(_)
        for _ in session.exec(select(Character)).all():
            session.delete(_)
            
        char = Character(id=1, name="TestChar", brass_coins=100)
        session.add(char)
        item = Item(id=1, name="Pickaxe", category="Equipment")
        session.add(item)
        session.commit()
        
        inv = Inventory(character_id=1, item_id=item.id, quantity=1, durability=100)
        session.add(inv)
        session.commit()
    yield

def test_empire_update_brass_coins():
    with Session(db_engine) as session:
        repo = StateRepository(session)
        # Test earning coins
        repo.apply_empire_update({"brass_coins_change": 50}, char_id=1)
        char = session.get(Character, 1)
        assert char.brass_coins == 150
        
        # Test spending coins
        repo.apply_empire_update({"brass_coins_change": -30}, char_id=1)
        session.refresh(char)
        assert char.brass_coins == 120

def test_tool_durability_update():
    with Session(db_engine) as session:
        repo = StateRepository(session)
        repo.apply_tool_durability_update({
            "tool_name": "Pickaxe",
            "durability_change": -15
        })
        
        inv = session.exec(select(Inventory).where(Inventory.character_id == 1)).first()
        assert inv is not None
        assert inv.durability == 85
        
        # Break tool
        repo.apply_tool_durability_update({
            "tool_name": "Pickaxe",
            "durability_change": -85
        })
        inv2 = session.exec(select(Inventory).where(Inventory.character_id == 1)).first()
        assert inv2 is None  # Should be deleted when durability <= 0
