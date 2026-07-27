"""Combat fidelity: the combatant is the antagonist the narration names (combat_updates.enemy),
not whatever NPC happens to be in the scene set. The extraction prompt must ask for `enemy`."""

from backend.database import NPC as DBNPC
from backend.database import Character, CombatSession, SQLModel, WorldState, engine
from backend.engine import NarrativeEngine
from backend.models import PlayerAction
from backend.models import WorldState as WSModel
from backend.repository import StateRepository
from sqlmodel import Session, select


class _RecordingClient:
    def __init__(self):
        self.prompt = ""

    def generate(self, **kwargs):
        self.prompt = kwargs.get("prompt", "")
        return {"choices": [{"message": {"content": "{}"}}]}


def test_extraction_prompt_asks_for_enemy():
    client = _RecordingClient()
    NarrativeEngine(vllm_client=client)._extract_state(
        PlayerAction(action_text="I attack the brass sentinel", character_id=1),
        WSModel(),
        "The brass sentinel lunges at you.",
    )
    assert "enemy" in client.prompt


def test_named_enemy_becomes_the_combatant():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        char = Character(name="Fighter", location_id="1")
        session.add(char)
        session.add(WorldState(current_location_id="1", is_combat_active=False, active_npcs_ids=[]))
        session.commit()
        session.refresh(char)
        cid = char.id

    with Session(engine) as session:
        StateRepository(session).apply_combat_update(
            {"is_combat_active": True, "enemy": "Brass Sentinel"}, cid
        )

    with Session(engine) as session:
        cs = session.exec(select(CombatSession).where(CombatSession.location_id == "1")).first()
        names = [p["name"] for p in cs.turn_order if p["type"] == "npc"]
        assert "Brass Sentinel" in names
        enemy = session.exec(select(DBNPC).where(DBNPC.name == "Brass Sentinel")).first()
        assert enemy is not None and enemy.is_hostile is True
