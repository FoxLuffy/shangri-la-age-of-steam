from backend.database import NPC, Bounty, Character, WorldState, get_session
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_bounty_generation_and_acceptance(monkeypatch):
    monkeypatch.setenv("VLLM_API_BASE", "http://fake-vllm")

    # Create character
    resp = client.post("/gameplay/characters", json={
        "name": "Bounty Hunter",
        "preset": "Wanderer"
    })
    char_data = resp.json()
    char_id = char_data["id"]

    # Fetch bounties (should generate some)
    resp = client.get(f"/gameplay/bounties?character_id={char_id}")
    assert resp.status_code == 200
    bounties_data = resp.json()
    assert len(bounties_data["available"]) >= 3
    assert len(bounties_data["active_ids"]) == 0

    bounty_to_accept = bounties_data["available"][0]

    # Accept bounty
    resp = client.post(f"/gameplay/bounties/accept?character_id={char_id}", json={"bounty_id": bounty_to_accept["id"]})
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # Verify it's active
    resp = client.get(f"/gameplay/bounties?character_id={char_id}")
    bounties_data = resp.json()
    assert bounty_to_accept["id"] in bounties_data["active_ids"]

def test_bounty_completion(monkeypatch):
    monkeypatch.setenv("VLLM_API_BASE", "http://fake-vllm")

    with get_session() as session:
        # Create character
        char = Character(name="Slayer", character_class="Wanderer", location_id="1", active_bounties=[], completed_bounties=[], brass_coins=0)
        session.add(char)

        # Create Bounty
        bounty = Bounty(title="Target Thug", description="Kill Thug", target_npc_type="Thug", reward_coins=100, status="active")
        session.add(bounty)

        # Create NPC
        npc = NPC(id="thug_1", name="Ugly Thug", location_id="1", hp=50, max_hp=50)
        session.add(npc)

        # Create WorldState
        ws = WorldState(is_combat_active=True, active_npcs_ids=["thug_1"])
        session.add(ws)

        session.commit()
        session.refresh(char)
        session.refresh(bounty)
        session.refresh(npc)

        char.active_bounties = [bounty.id]
        session.add(char)
        session.commit()

        from backend.repository import StateRepository
        repo = StateRepository(session)

        # apply combat update to kill NPC
        update = {
            "npc_updates": [
                {"npc_id": npc.id, "hp_change": -50}
            ]
        }
        repo.apply_combat_update(update, char.id)

        session.refresh(char)
        session.refresh(bounty)

        assert bounty.status == "completed"
        assert char.brass_coins == 100
        assert bounty.id in char.completed_bounties
        assert bounty.id not in char.active_bounties
