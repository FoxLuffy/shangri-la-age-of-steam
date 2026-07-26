import hashlib

from backend.database import SQLModel, User, engine
from backend.database_init import seed_demo_user
from backend.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session, select

client = TestClient(app)


def fresh_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def test_seed_creates_non_admin_demo_user():
    fresh_db()
    seed_demo_user()
    with Session(engine) as session:
        demo = session.exec(select(User).where(User.username == "demo")).first()
        assert demo is not None
        assert demo.is_admin is False
        assert demo.password_hash == hashlib.sha256(b"demo").hexdigest()


def test_seed_is_idempotent():
    fresh_db()
    seed_demo_user()
    seed_demo_user()
    with Session(engine) as session:
        demos = session.exec(select(User).where(User.username == "demo")).all()
        assert len(demos) == 1


def test_demo_can_log_in_as_normal_user():
    fresh_db()
    seed_demo_user()
    resp = client.post("/auth/login", json={"username": "demo", "password": "demo"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_admin"] is False
    assert body["token"]
