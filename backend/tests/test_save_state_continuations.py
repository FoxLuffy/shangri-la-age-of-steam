from backend.database import Character, SQLModel, User, engine
from backend.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session

client = TestClient(app)


def setup_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(username="testuser", password_hash="hash")
        session.add(user)
        session.commit()
        session.refresh(user)

        char1 = Character(user_id=user.id, name="TestChar1", character_class="Wanderer")
        char2 = Character(user_id=user.id, name="TestChar2", character_class="Aristocrat")
        session.add(char1)
        session.add(char2)
        session.commit()
        return user.id


def test_get_user_sessions():
    user_id = setup_db()

    response = client.get(f"/sessions/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "TestChar1"
    assert data[1]["name"] == "TestChar2"
