"""Combat should start from natural play: the extraction prompt must instruct the model
to emit combat_updates, and apply_combat_update must start a CombatSession."""

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


def test_extraction_prompt_instructs_combat_updates():
    client = _RecordingClient()
    eng = NarrativeEngine(vllm_client=client)
    eng._extract_state(
        PlayerAction(action_text="I swing my wrench at the automaton", character_id=1),
        WSModel(),
        "You strike the automaton and it reels.",
    )
    assert "COMBAT" in client.prompt
    assert "is_combat_active" in client.prompt


def test_apply_combat_update_starts_a_session():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        char = Character(name="Fighter", location_id="1")
        session.add(char)
        session.add(WorldState(current_location_id="1", is_combat_active=False))
        session.commit()
        session.refresh(char)
        cid = char.id

    with Session(engine) as session:
        StateRepository(session).apply_combat_update({"is_combat_active": True}, cid)

    with Session(engine) as session:
        cs = session.exec(select(CombatSession).where(CombatSession.location_id == "1")).first()
        assert cs is not None and cs.is_active is True
        db_state = session.exec(select(WorldState).order_by(WorldState.id.desc())).first()
        assert db_state.is_combat_active is True
