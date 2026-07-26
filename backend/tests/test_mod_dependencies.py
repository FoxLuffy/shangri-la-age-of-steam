from backend.database import Faction, Location, SQLModel, engine
from backend.main import app, resolve_install_order
from fastapi.testclient import TestClient
from sqlmodel import Session

client = TestClient(app)


def fresh_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


# --- pure resolver ---

REG = [
    {"id": "a", "dependencies": ["b"]},
    {"id": "b", "dependencies": ["c"]},
    {"id": "c", "dependencies": []},
]


def test_resolver_orders_dependencies_first():
    res = resolve_install_order(REG, "a")
    assert res["cycle"] is False
    assert res["missing"] == []
    # c before b before a
    assert res["order"].index("c") < res["order"].index("b") < res["order"].index("a")
    assert res["order"][-1] == "a"


def test_resolver_flags_missing_dependency():
    reg = [{"id": "a", "dependencies": ["ghost"]}]
    res = resolve_install_order(reg, "a")
    assert "ghost" in res["missing"]
    assert res["order"] == ["a"]


def test_resolver_detects_cycle():
    reg = [
        {"id": "x", "dependencies": ["y"]},
        {"id": "y", "dependencies": ["x"]},
    ]
    res = resolve_install_order(reg, "x")
    assert res["cycle"] is True


# --- endpoints (use the real registry: mod_2 depends on mod_1) ---


def test_dependencies_endpoint_returns_order():
    res = client.get("/workshop/mods/mod_2/dependencies")
    assert res.status_code == 200
    order = res.json()["order"]
    assert order == ["mod_1", "mod_2"]


def test_dependencies_unknown_mod_404():
    assert client.get("/workshop/mods/nope/dependencies").status_code == 404


def test_install_installs_dependencies_first():
    fresh_db()
    res = client.post("/workshop/mods/mod_2/install")
    assert res.status_code == 200
    installed = res.json()["installed"]
    assert installed.index("mod_1") < installed.index("mod_2")

    # Both mods' entities landed.
    with Session(engine) as session:
        assert session.get(Location, "mod_sky_docks") is not None
        assert session.get(Faction, "mod_sky_pirates") is not None


def test_install_missing_dependency_warns(monkeypatch):
    fresh_db()

    reg = [{"id": "solo", "name": "Solo", "dependencies": ["ghost"]}]
    monkeypatch.setattr("backend.main._load_workshop_registry", lambda: reg)
    # No solo.json file exists → warning for the missing file too, but the missing
    # dependency 'ghost' must be reported.
    res = client.post("/workshop/mods/solo/install")
    assert res.status_code == 200
    warnings = " ".join(res.json()["warnings"])
    assert "ghost" in warnings
