"""Artifact + character routes. These use `with get_session()` (the same pattern as every
other gameplay route) rather than Depends(get_session) — the latter yields the
@contextmanager object instead of a Session and 500s in production (it only appeared to work
in tests via dependency_overrides). So we exercise the real routes against the real engine."""

import pytest
from backend.database import Artifact, Character, SQLModel, engine
from backend.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session, select

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    # Ensure the shared schema exists and start from clean Artifact/Character rows. Do NOT
    # drop_all the shared engine here — other TestClient-based tests read the same engine and
    # would hit missing tables depending on execution order.
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for row in session.exec(select(Artifact)).all():
            session.delete(row)
        for row in session.exec(select(Character)).all():
            session.delete(row)
        session.commit()
    yield


def test_get_artifacts():
    with Session(engine) as session:
        session.add(
            Artifact(name="Test Artifact", description="A test artifact", stat_bonus={"strength": 5}, rarity="Legendary")
        )
        session.commit()

    response = client.get("/gameplay/artifacts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Artifact"


def test_discover_artifact():
    with Session(engine) as session:
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

    with Session(engine) as session:
        char = session.get(Character, char_id)
        assert artifact_id in char.discovered_artifacts

    # Stats bonus applied on character load.
    response = client.get(f"/gameplay/characters/{char_id}")
    assert response.status_code == 200
    assert response.json()["stats"]["strength"] == 15
