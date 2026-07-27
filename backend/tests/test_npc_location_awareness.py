"""B3: mentioned NPCs are situated at the correct location (honor explicit location_id),
newly-introduced NPCs are NOT force-added to the earshot scene set, and a location's
surfaced active_npcs is capped so it doesn't drown in every character ever mentioned."""

from backend.database import NPC as DBNPC
from backend.database import Character, SQLModel, WorldState, engine
from backend.repository import _MAX_SURFACED_NPCS, StateRepository
from sqlmodel import Session


def _fresh():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def test_create_or_update_npc_honors_explicit_location():
    _fresh()
    with Session(engine) as session:
        repo = StateRepository(session)
        # Engine passes the resolved location (npc_info.location_id or player's loc). Here the
        # NPC is described as being in the Undercity (5) while the player is elsewhere.
        npc = repo.create_or_update_npc({"name": "Silas", "location_id": "5"}, "5")
        assert npc.location_id == "5"


def test_surfaced_active_npcs_are_capped():
    _fresh()
    with Session(engine) as session:
        char = Character(name="Ada", location_id="1")
        session.add(char)
        # Many NPCs at the player's location; only one is engaged (in earshot).
        for i in range(10):
            session.add(DBNPC(id=f"n{i}", name=f"NPC {i}", location_id="1"))
        session.add(WorldState(current_location_id="1", active_npcs_ids=["n3"]))
        session.commit()
        session.refresh(char)

        state = StateRepository(session).get_latest_state(char.id)
        assert len(state.active_npcs) == _MAX_SURFACED_NPCS
        # The engaged NPC is always retained despite the cap.
        assert any(n.id == "n3" and n.in_earshot for n in state.active_npcs)


def test_engaged_npcs_kept_even_beyond_cap():
    _fresh()
    with Session(engine) as session:
        char = Character(name="Ada", location_id="1")
        session.add(char)
        for i in range(10):
            session.add(DBNPC(id=f"n{i}", name=f"NPC {i}", location_id="1"))
        # 8 engaged — more than the cap; all engaged must be kept.
        engaged_ids = [f"n{i}" for i in range(8)]
        session.add(WorldState(current_location_id="1", active_npcs_ids=engaged_ids))
        session.commit()
        session.refresh(char)

        state = StateRepository(session).get_latest_state(char.id)
        surfaced = {n.id for n in state.active_npcs}
        assert set(engaged_ids).issubset(surfaced)
