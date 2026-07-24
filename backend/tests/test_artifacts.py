import contextlib
from unittest.mock import patch

import pytest
from backend.database import Artifact, Character
from backend.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from sqlalchemy.pool import StaticPool
sqlite_url = "sqlite:///:memory:"
test_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)

def get_session_override():
    with Session(test_engine) as session:
        yield session

client = TestClient(app)

from backend.database import get_session

@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(test_engine)
    app.dependency_overrides[get_session] = get_session_override
    yield
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(test_engine)

def test_get_artifacts():
    with Session(test_engine) as session:
        artifact = Artifact(name="Test Artifact", description="A test artifact", stat_bonus={"strength": 5}, rarity="Legendary")
        session.add(artifact)
        session.commit()

    response = client.get("/gameplay/artifacts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Artifact"

def test_discover_artifact():
    with Session(test_engine) as session:
        char = Character(name="Hero", user_id=1, stats={"strength": 10})
        artifact = Artifact(name="Sword of Truth", description="Very sharp", stat_bonus={"strength": 5}, rarity="Epic")
        session.add(char)
        session.add(artifact)
        session.commit()
        session.refresh(char)
        session.refresh(artifact)
        char_id = char.id
        artifact_id = artifact.id

    response = client.post(f"/gameplay/artifacts/discover?character_id={char_id}&artifact_id={artifact_id}")
    assert response.status_code == 200

    with Session(test_engine) as session:
        char = session.get(Character, char_id)
        assert artifact_id in char.discovered_artifacts

    # Check stats applied on load
    response = client.get(f"/gameplay/characters/{char_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["stats"]["strength"] == 15
