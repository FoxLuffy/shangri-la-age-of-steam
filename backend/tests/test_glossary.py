from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_get_glossary():
    response = client.get("/glossary")
    assert response.status_code == 200
    data = response.json()
    assert "locations" in data
    assert "npcs" in data
    assert "items" in data
    assert isinstance(data["locations"], list)
    assert isinstance(data["npcs"], list)
    assert isinstance(data["items"], list)
