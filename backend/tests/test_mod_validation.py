import io
import json
import os

from backend.database import Location, SQLModel, engine
from backend.main import app
from backend.mod_validation import validate_mod
from fastapi.testclient import TestClient
from sqlmodel import Session

client = TestClient(app)

EXAMPLE_MOD = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "mods", "example_mod.json")


def fresh_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _validate(data):
    fresh_db()
    with Session(engine) as session:
        return validate_mod(data, session)


def test_valid_example_has_no_errors():
    with open(EXAMPLE_MOD) as f:
        data = json.load(f)
    assert _validate(data) == []


def test_missing_required_field():
    errors = _validate({"factions": [{"id": "f1"}]})  # no name/description
    assert errors
    assert any("name" in e for e in errors)


def test_wrong_type():
    errors = _validate(
        {"npcs": [{"id": "n1", "name": "Bot", "disposition": "high"}]}
    )
    assert any("disposition" in e for e in errors)


def test_unknown_field_rejected():
    errors = _validate({"factions": [{"id": "f1", "name": "F", "description": "d", "colour": "red"}]})
    assert any("colour" in e for e in errors)


def test_invalid_item_category():
    errors = _validate({"items": [{"name": "Thing", "category": "Bananas"}]})
    assert any("category" in e.lower() for e in errors)


def test_duplicate_id_in_file():
    errors = _validate(
        {
            "factions": [
                {"id": "dup", "name": "A", "description": "x"},
                {"id": "dup", "name": "B", "description": "y"},
            ]
        }
    )
    assert any("duplicate" in e.lower() for e in errors)


def test_dangling_reference_rejected():
    errors = _validate(
        {"npcs": [{"id": "n1", "name": "Bot", "location_id": "nowhere"}]}
    )
    assert any("nowhere" in e for e in errors)


def test_same_file_reference_resolves():
    data = {
        "locations": [{"id": "loc_x", "name": "X", "description": "d"}],
        "npcs": [{"id": "n1", "name": "Bot", "location_id": "loc_x"}],
    }
    assert _validate(data) == []


def test_reference_to_existing_db_location_resolves():
    fresh_db()
    with Session(engine) as session:
        session.add(Location(id="db_loc", name="DB", description="d"))
        session.commit()
        errors = validate_mod({"npcs": [{"id": "n1", "name": "Bot", "location_id": "db_loc"}]}, session)
    assert errors == []


def test_collects_multiple_errors():
    errors = _validate(
        {
            "factions": [{"id": "f1"}],  # missing name/description
            "items": [{"name": "Thing", "category": "Bananas"}],  # bad category
        }
    )
    assert len(errors) >= 2


def test_upload_endpoint_rejects_invalid_with_list_detail():
    fresh_db()
    payload = json.dumps({"factions": [{"id": "f1"}]}).encode()
    resp = client.post(
        "/modding/upload",
        files={"file": ("bad.json", io.BytesIO(payload), "application/json")},
    )
    assert resp.status_code == 400
    assert isinstance(resp.json()["detail"], list)


def test_upload_endpoint_accepts_valid_example():
    fresh_db()
    with open(EXAMPLE_MOD, "rb") as f:
        raw = f.read()
    resp = client.post(
        "/modding/upload",
        files={"file": ("example_mod.json", io.BytesIO(raw), "application/json")},
    )
    assert resp.status_code == 200
