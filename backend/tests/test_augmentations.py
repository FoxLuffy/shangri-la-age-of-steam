from backend.database import Character, get_session
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_get_augmentation_catalog():
    response = client.get("/gameplay/augmentations/catalog")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "pneumatic_arm" in [a["id"] for a in data]

def test_install_augmentation():
    # First create a test character in DB with enough coins
    with get_session() as session:
        char = Character(name="Aug Test Char", brass_coins=500, total_strain=0)
        session.add(char)
        session.commit()
        session.refresh(char)
        char_id = char.id

    payload = {
        "character_id": char_id,
        "augmentation_id": "pneumatic_arm"
    }
    response = client.post("/gameplay/augmentations/install", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    aug_data = data.get("augmentation", {})
    assert aug_data.get("augmentation_name") == "Pneumatic Arm", f"Data: {data}"
    assert data["character_strain"] == 10
    assert data["brass_coins"] == 300  # 500 - 200

def test_install_augmentation_not_enough_coins():
    # Character with 0 coins
    with get_session() as session:
        char = Character(name="Poor Char", brass_coins=0, total_strain=0)
        session.add(char)
        session.commit()
        session.refresh(char)
        char_id = char.id

    payload = {
        "character_id": char_id,
        "augmentation_id": "pneumatic_arm"
    }
    response = client.post("/gameplay/augmentations/install", json=payload)
    assert response.status_code == 400
    assert "Not enough brass coins" in response.json()["detail"]
