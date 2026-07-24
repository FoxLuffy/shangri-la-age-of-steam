from contextlib import contextmanager
from unittest.mock import patch

import pytest
from backend.database import Character, Location
from backend.main import app
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    @contextmanager
    def mock_get_session():
        yield session

    with patch("backend.routers.gameplay.get_session", mock_get_session):
        client = TestClient(app)
        yield client

def test_trade_system(client: TestClient, session: Session):
    c1 = Character(name="Alice", brass_coins=100)
    c2 = Character(name="Bob", brass_coins=50)
    session.add(c1)
    session.add(c2)
    session.commit()
    session.refresh(c1)
    session.refresh(c2)

    res = client.post(f"/gameplay/trade/offer?initiator_id={c1.id}", json={
        "receiver_id": c2.id,
        "initiator_coins": 10,
        "receiver_coins": 5
    })
    assert res.status_code == 200
    trade_id = res.json()["id"]

    res = client.post(f"/gameplay/trade/accept?character_id={c2.id}", json={
        "trade_id": trade_id,
        "accept": True
    })
    assert res.status_code == 200

    session.refresh(c1)
    session.refresh(c2)
    assert c1.brass_coins == 95
    assert c2.brass_coins == 55

def test_guild_system(client: TestClient, session: Session):
    c1 = Character(name="Alice")
    c2 = Character(name="Bob")
    session.add(c1)
    session.add(c2)
    session.commit()
    session.refresh(c1)
    session.refresh(c2)

    res = client.post(f"/gameplay/guilds/create?character_id={c1.id}", json={"name": "TestGuild", "description": "Test"})
    assert res.status_code == 200
    print(res.json())
    guild_id = res.json()["id"]

    res = client.post(f"/gameplay/guilds/invite?leader_id={c1.id}", json={"guild_id": guild_id, "character_id": c2.id})
    assert res.status_code == 200

    res = client.get(f"/gameplay/guilds/treasury?guild_id={guild_id}")
    assert res.status_code == 200
    assert res.json()["treasury"] == 0
    assert "Alice" in res.json()["members"]
    assert "Bob" in res.json()["members"]

def test_bulletin_board(client: TestClient, session: Session):
    loc = Location(id="1", name="Town", description="A town")
    c1 = Character(name="Alice")
    session.add(loc)
    session.add(c1)
    session.commit()
    session.refresh(c1)

    res = client.post(f"/gameplay/messages/send?character_id={c1.id}", json={"location_id": "1", "content": "Hello World!"})
    assert res.status_code == 200

    res = client.get("/gameplay/messages/board?location_id=1")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["content"] == "Hello World!"
