from unittest.mock import patch

import pytest
from backend.database import Character
from backend.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

sqlite_url = "sqlite:///test_crafting.db"
engine = create_engine(sqlite_url, echo=False, connect_args={'check_same_thread': False})

@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
def session():
    with Session(engine) as session:
        yield session

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_character(session: Session):
    char = Character(
        name="TestCrafter",
        character_class="Alchemist",
        known_recipes=["basic_potion"],
        crafting_proficiencies={"Alchemy": 5}
    )
    session.add(char)
    session.commit()
    session.refresh(char)
    return char

def test_discover_recipe(client: TestClient, test_character: Character, session: Session):
    with patch("backend.routers.gameplay.get_session") as mock_get_session:
        mock_get_session.return_value.__enter__.return_value = session

        response = client.post("/gameplay/crafting/discover", json={
            "character_id": test_character.id,
            "recipe_id": "advanced_potion"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "advanced_potion" in data["known_recipes"]

        # Verify in DB
        session.refresh(test_character)
        assert "advanced_potion" in test_character.known_recipes

def test_craft_unknown_recipe_fails(client: TestClient, test_character: Character, session: Session):
    with patch("backend.routers.gameplay.get_session") as mock_get_session:
        mock_get_session.return_value.__enter__.return_value = session
        response = client.post("/gameplay/craft", json={
            "character_id": test_character.id,
            "recipe_id": "copper_wire",
            "branch": "Metallurgy"
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "Recipe not known"

def test_craft_known_recipe_success_prob(client: TestClient, test_character: Character, session: Session):
    with patch("backend.routers.gameplay.get_session") as mock_get_session, patch("random.random", return_value=0.1):
        mock_get_session.return_value.__enter__.return_value = session
        response = client.post("/gameplay/craft", json={
            "character_id": test_character.id,
            "recipe_id": "basic_potion",
            "branch": "Alchemy"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["probability"] == 0.95
