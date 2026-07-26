from backend.database import MainQuest, SQLModel, User, engine
from backend.database_init import seed_demo_user
from backend.main import app
from backend.main_quests import generate_main_quest, preset_list
from backend.repository import StateRepository
from fastapi.testclient import TestClient
from sqlmodel import Session, select

client = TestClient(app)


def fresh():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _demo_id():
    seed_demo_user()
    with Session(engine) as session:
        return session.exec(select(User).where(User.username == "demo")).first().id


# --- presets & generation ---

def test_presets_have_staged_objectives():
    presets = preset_list()
    assert len(presets) >= 3
    for p in presets:
        assert p["title"] and isinstance(p["stages"], list) and len(p["stages"]) >= 3


def test_generate_parses_llm_json():
    class FakeClient:
        def generate(self, **kw):
            return {"choices": [{"text": '{"title":"The Cog War","description":"d","stages":["a","b","c","d"]}'}]}

    q = generate_main_quest(FakeClient(), "Alchemist", "Guild Apprentice", "bg")
    assert q["title"] == "The Cog War"
    assert q["stages"] == ["a", "b", "c", "d"]


def test_generate_falls_back_to_preset_on_error():
    class BoomClient:
        def generate(self, **kw):
            raise RuntimeError("vllm down")

    q = generate_main_quest(BoomClient())
    assert q["title"] and len(q["stages"]) >= 3  # a preset


def test_main_quests_endpoint():
    resp = client.get("/main-quests")
    assert resp.status_code == 200
    assert len(resp.json()) >= 3


# --- creation attach + read + advance ---

def _create_with_quest(cid_user):
    return client.post("/characters", json={
        "name": "Arc Hero", "preset": "Alchemist", "origin": "Guild Apprentice",
        "backstory": "", "gear": [], "user_id": cid_user,
        "main_quest": {"title": "The Aether Heart", "description": "Recover it.",
                       "stages": ["Find the apprentice", "Steal the schematic", "Assemble it"]},
    })


def test_create_character_attaches_main_quest_stage0_active():
    fresh()
    uid = _demo_id()
    cid = _create_with_quest(uid).json()["id"]
    with Session(engine) as session:
        mq = session.exec(select(MainQuest).where(MainQuest.character_id == cid)).first()
        assert mq is not None
        assert mq.current_stage == 0
        assert mq.stages[0]["status"] == "active"
        assert all(s["status"] == "pending" for s in mq.stages[1:])


def test_get_main_quest_returns_current_objective():
    fresh()
    uid = _demo_id()
    cid = _create_with_quest(uid).json()["id"]
    resp = client.get(f"/main-quest/{cid}")
    assert resp.status_code == 200
    assert resp.json()["current_objective"] == "Find the apprentice"


def test_advance_main_quest_moves_and_completes():
    fresh()
    uid = _demo_id()
    cid = _create_with_quest(uid).json()["id"]
    with Session(engine) as session:
        repo = StateRepository(session)
        repo.advance_main_quest(cid)  # stage 0 -> 1
    assert client.get(f"/main-quest/{cid}").json()["current_objective"] == "Steal the schematic"

    with Session(engine) as session:
        repo = StateRepository(session)
        repo.advance_main_quest(cid)  # -> stage 2
        repo.advance_main_quest(cid)  # -> complete
        mq = session.exec(select(MainQuest).where(MainQuest.character_id == cid)).first()
        assert mq.status == "completed"
        assert all(s["status"] == "done" for s in mq.stages)


def test_prompt_includes_current_main_quest_objective():
    fresh()
    uid = _demo_id()
    cid = _create_with_quest(uid).json()["id"]
    from backend.models import PlayerAction
    from backend.prompt_utils import build_narrative_prompt
    with Session(engine) as session:
        state = StateRepository(session).get_latest_state(cid)
    prompt = build_narrative_prompt(state, PlayerAction(action_text="look around", character_id=cid))
    assert "MAIN QUEST" in prompt
    assert "Find the apprentice" in prompt


def test_get_main_quest_404_when_none():
    fresh()
    uid = _demo_id()
    cid = client.post("/characters", json={
        "name": "No Arc", "preset": "Wanderer", "origin": "", "backstory": "", "gear": [], "user_id": uid,
    }).json()["id"]
    assert client.get(f"/main-quest/{cid}").status_code == 404
