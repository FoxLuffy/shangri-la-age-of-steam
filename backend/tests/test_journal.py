"""C2: the Explorer's Journal populates from real play — locations visited, NPCs met, and a
seeded artifact codex with discovery. Fixes the empty journal (report #7)."""

import asyncio

from backend.database import NPC as DBNPC
from backend.database import Artifact, Character, Location, SQLModel, engine
from backend.database_init import seed_data
from backend.repository import StateRepository
from backend.routers.gameplay import get_journal
from sqlmodel import Session, select


def _fresh():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def test_seed_data_seeds_artifacts():
    _fresh()
    seed_data()
    with Session(engine) as session:
        assert len(session.exec(select(Artifact)).all()) > 0


def test_record_discoveries_logs_places_and_people_idempotently():
    _fresh()
    with Session(engine) as session:
        char = Character(name="Explorer", location_id="1")
        session.add(char)
        session.commit()
        session.refresh(char)
        cid = char.id

        repo = StateRepository(session)
        repo.record_discoveries(cid, "1", ["silas"])
        repo.record_discoveries(cid, "1", ["silas", "mara"])  # dupes ignored, mara added

        session.refresh(char)
        assert char.visited_locations == ["1"]
        assert char.met_npcs == ["silas", "mara"]


def test_discover_artifact_by_name():
    _fresh()
    with Session(engine) as session:
        char = Character(name="Explorer", location_id="1")
        session.add(char)
        session.add(Artifact(id=1, name="Aether Compass", description="d", stat_bonus={}, rarity="Rare"))
        session.commit()
        session.refresh(char)

        art = StateRepository(session).discover_artifact_by_name(char.id, "aether compass")
        assert art and art.id == 1
        session.refresh(char)
        assert char.discovered_artifacts == [1]


def test_journal_endpoint_returns_populated_sections():
    _fresh()
    with Session(engine) as session:
        session.add(Location(id="1", name="The Rusty Anchor Tavern", description="A dim tavern."))
        session.add(DBNPC(id="silas", name="Silas", location_id="1"))
        session.add(Artifact(id=1, name="Aether Compass", description="d", stat_bonus={}, rarity="Rare"))
        session.add(Artifact(id=2, name="Ironheart Locket", description="d", stat_bonus={}, rarity="Uncommon"))
        char = Character(
            name="Explorer", location_id="1", visited_locations=["1"], met_npcs=["silas"], discovered_artifacts=[1]
        )
        session.add(char)
        session.commit()
        session.refresh(char)
        cid = char.id

    data = asyncio.run(get_journal(cid))
    assert [p["name"] for p in data["places"]] == ["The Rusty Anchor Tavern"]
    assert [p["name"] for p in data["people"]] == ["Silas"]
    by_id = {a["id"]: a for a in data["artifacts"]}
    assert by_id[1]["discovered"] is True
    assert by_id[2]["discovered"] is False


def test_journal_and_artifacts_routes_work_through_fastapi():
    """Regression: these routes previously used Depends(get_session) on a @contextmanager,
    which yielded the context-manager object instead of a Session and 500'd at runtime
    (unit tests that call the function with a real Session missed it). Exercise the real
    routes through the app."""
    from backend.main import app
    from fastapi.testclient import TestClient

    _fresh()
    with Session(engine) as session:
        session.add(Artifact(id=1, name="Aether Compass", description="d", stat_bonus={}, rarity="Rare"))
        char = Character(name="Explorer", location_id="1", visited_locations=[], met_npcs=[], discovered_artifacts=[])
        session.add(char)
        session.commit()
        session.refresh(char)
        cid = char.id

    client = TestClient(app)
    assert client.get("/gameplay/artifacts").status_code == 200
    r = client.get(f"/gameplay/journal?character_id={cid}")
    assert r.status_code == 200, r.text
    assert "artifacts" in r.json()
    assert client.get(f"/gameplay/characters/{cid}").status_code == 200
