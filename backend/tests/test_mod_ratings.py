from backend.database import SQLModel, engine
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def fresh_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _mod(mods, mod_id):
    return next(m for m in mods if m["id"] == mod_id)


def test_rate_updates_aggregates():
    fresh_db()
    r = client.post("/workshop/mods/mod_1/rate", json={"user_id": 1, "stars": 4, "review": "solid"})
    assert r.status_code == 200
    assert r.json()["rating_count"] == 1

    mod = _mod(client.get("/workshop/mods").json(), "mod_1")
    assert mod["avg_rating"] == 4.0
    assert mod["rating_count"] == 1


def test_rerate_upserts_same_row():
    fresh_db()
    client.post("/workshop/mods/mod_1/rate", json={"user_id": 1, "stars": 2})
    client.post("/workshop/mods/mod_1/rate", json={"user_id": 1, "stars": 5})

    mod = _mod(client.get("/workshop/mods").json(), "mod_1")
    assert mod["rating_count"] == 1
    assert mod["avg_rating"] == 5.0


def test_invalid_stars_rejected():
    fresh_db()
    assert client.post("/workshop/mods/mod_1/rate", json={"user_id": 1, "stars": 0}).status_code == 400
    assert client.post("/workshop/mods/mod_1/rate", json={"user_id": 1, "stars": 6}).status_code == 400


def test_average_of_multiple_users():
    fresh_db()
    client.post("/workshop/mods/mod_1/rate", json={"user_id": 1, "stars": 3})
    client.post("/workshop/mods/mod_1/rate", json={"user_id": 2, "stars": 5})

    mod = _mod(client.get("/workshop/mods").json(), "mod_1")
    assert mod["rating_count"] == 2
    assert mod["avg_rating"] == 4.0


def test_high_rating_marks_featured():
    fresh_db()
    mod = _mod(client.get("/workshop/mods").json(), "mod_1")
    assert mod["featured"] is False

    client.post("/workshop/mods/mod_1/rate", json={"user_id": 1, "stars": 5})
    mod = _mod(client.get("/workshop/mods").json(), "mod_1")
    assert mod["featured"] is True


def test_ratings_list_returns_reviews():
    fresh_db()
    client.post("/workshop/mods/mod_1/rate", json={"user_id": 7, "stars": 4, "review": "gears galore"})
    resp = client.get("/workshop/mods/mod_1/ratings")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["user_id"] == 7
    assert data[0]["review"] == "gears galore"
