"""D1: NPC dialogue is captured each turn (npc_dialogue) and stored as current_dialogue, so
the 'Show Dialogue' control shows a real, updating line instead of 'No current dialogue'."""

from backend.database import NPC as DBNPC
from backend.database import Character, SQLModel, WorldState, engine
from backend.repository import StateRepository
from sqlmodel import Session, select


def _fresh():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def test_apply_npc_dialogue_sets_and_updates_current_dialogue():
    _fresh()
    with Session(engine) as session:
        session.add(DBNPC(id="silas", name="Silas the Smuggler", location_id="1"))
        session.commit()
        repo = StateRepository(session)

        # Matches by containment (model uses the short name).
        repo.apply_npc_dialogue([{"name": "Silas", "line": "Keep your voice down."}], "1")
        npc = session.get(DBNPC, "silas")
        assert npc.current_dialogue == "Keep your voice down."

        # A later turn updates it.
        repo.apply_npc_dialogue([{"name": "Silas the Smuggler", "line": "The cargo's moved."}], "1")
        session.refresh(npc)
        assert npc.current_dialogue == "The cargo's moved."


def test_apply_npc_dialogue_creates_missing_npc():
    _fresh()
    with Session(engine) as session:
        StateRepository(session).apply_npc_dialogue([{"name": "Mara", "line": "New here?"}], "3")
        npc = session.exec(select(DBNPC).where(DBNPC.name == "Mara")).first()
        assert npc is not None and npc.current_dialogue == "New here?" and npc.location_id == "3"


def test_ignores_blank_entries():
    _fresh()
    with Session(engine) as session:
        StateRepository(session).apply_npc_dialogue(
            [{"name": "", "line": "x"}, {"name": "Ghost", "line": ""}, "not a dict"], "1"
        )
        assert session.exec(select(DBNPC)).all() == []


def test_current_dialogue_surfaces_in_state():
    _fresh()
    with Session(engine) as session:
        char = Character(name="Ada", location_id="1")
        session.add(char)
        session.add(DBNPC(id="silas", name="Silas", location_id="1", current_dialogue="Well met."))
        session.add(WorldState(current_location_id="1"))
        session.commit()
        session.refresh(char)

        state = StateRepository(session).get_latest_state(char.id)
        silas = next(n for n in state.active_npcs if n.id == "silas")
        assert silas.current_dialogue == "Well met."
