from backend.database import engine as db_engine
from backend.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session


def test_gear_lock_minigame():
    from backend.database import Character

    with Session(db_engine) as session:
        char = Character(name="Spy")
        session.add(char)
        session.commit()

        client = TestClient(app)

        # 1. Start minigame
        res1 = client.post(f"/minigames/start?character_id={char.id}&game_type=gear_lock")
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["type"] == "gear_lock"
        assert not data1["solved"]
        game_id = data1["id"]

        # 2. Perform an action to solve
        # A gear lock might start with all 0s and need to reach 5s. We'll just mock it or force a win
        # For the test, we'll hit an endpoint that just tries to solve it directly or increments a gear.

        res2 = client.post(f"/minigames/{game_id}/action", json={"action": "solve_cheat"})
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["solved"] is True


def test_hack_mastermind_minigame():
    from backend.database import Character, Minigame

    with Session(db_engine) as session:
        char = Character(name="Hacker")
        session.add(char)
        session.commit()

        client = TestClient(app)

        # Create a mock minigame
        state = {
            "sequence": ["A", "B", "C"],
            "guesses": [],
            "current_input": [],
            "attempts_left": 3,
            "message": "Terminal locked.",
            "hint_revealed": False,
        }
        mg = Minigame(character_id=char.id, type="hack", state=state, solved=False)
        session.add(mg)
        session.commit()

        # Test incorrect guess
        res = client.post("/minigame/play", json={"minigame_id": mg.id, "action": "input", "data": {"value": "C"}})
        res = client.post("/minigame/play", json={"minigame_id": mg.id, "action": "input", "data": {"value": "B"}})
        res = client.post("/minigame/play", json={"minigame_id": mg.id, "action": "input", "data": {"value": "D"}})
        data = res.json()["state"]

        # Should have 1 guess, 1 correct pos (B), 1 correct char (C)
        assert len(data["guesses"]) == 1
        assert data["guesses"][0]["correct_pos"] == 1
        assert data["guesses"][0]["correct_char"] == 1
        assert data["attempts_left"] == 2

        # Test correct guess
        res = client.post("/minigame/play", json={"minigame_id": mg.id, "action": "input", "data": {"value": "A"}})
        res = client.post("/minigame/play", json={"minigame_id": mg.id, "action": "input", "data": {"value": "B"}})
        res = client.post("/minigame/play", json={"minigame_id": mg.id, "action": "input", "data": {"value": "C"}})

        data2 = res.json()
        assert data2["solved"] is True
