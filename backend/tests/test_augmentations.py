import pytest
from sqlmodel import Session, select
from backend.main import app
from backend.database import engine as db_engine, get_session
from fastapi.testclient import TestClient

def test_install_augmentation():
    from backend.database import Character, Augmentation
    with Session(db_engine) as session:
        # Create character if not exists
        char = session.exec(select(Character).where(Character.id == 1)).first()
        if not char:
            char = Character(id=1, name="Player")
            session.add(char)
            session.commit()
            session.refresh(char)

        # Install augmentation
        aug = Augmentation(
            character_id=char.id,
            body_part="left_arm",
            augmentation_name="Pneumatic Fist",
            stat_bonus={"strength": 5.0}
        )
        session.add(aug)
        session.commit()
        session.refresh(aug)

        assert aug.id is not None
        assert aug.augmentation_name == "Pneumatic Fist"
        assert aug.stat_bonus.get("strength") == 5.0

def test_api_get_augmentations():
    client = TestClient(app)
    response = client.get("/augmentations?character_id=1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    names = [a["augmentation_name"] for a in data]
    assert "Pneumatic Fist" in names
