"""CR4: NPCs missing from the Environment overview.

active_npcs must be the union of NPCs physically at the character's location AND the
NPCs the engine tracked in world_state.active_npcs_ids (conversation partners; survivors
of world events). Previously it was location-only, so conversation NPCs (#6) and NPCs
after a dynamic event (#3) vanished.
"""

from backend.database import NPC as DBNPC
from backend.database import Character, Location, SQLModel, WorldState, engine
from backend.repository import StateRepository
from sqlmodel import Session


def setup_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Location(id="A", name="Foundry", description=""))
        session.add(Location(id="B", name="Docks", description=""))
        char = Character(name="Hero", location_id="A")
        session.add(char)
        # present_npc: at the location. convo_npc: in scene AND at the location.
        # follower_npc: in scene but at a DIFFERENT location (must NOT follow).
        session.add(DBNPC(id="present_npc", name="Gearsmith", location_id="A"))
        session.add(DBNPC(id="convo_npc", name="Sly the Fox", location_id="A"))
        session.add(DBNPC(id="follower_npc", name="Kaelen", location_id="B"))
        session.add(WorldState(current_location_id="A", active_npcs_ids=["convo_npc", "follower_npc"]))
        session.commit()
        session.refresh(char)
        return char.id


def test_active_npcs_include_location_and_in_scene_here():
    cid = setup_db()
    with Session(engine) as session:
        state = StateRepository(session).get_latest_state(cid)
    ids = {npc.id for npc in state.active_npcs}
    assert "present_npc" in ids     # at the location
    assert "convo_npc" in ids       # in scene AND at this location


def test_scene_npc_at_other_location_does_not_follow():
    cid = setup_db()
    with Session(engine) as session:
        state = StateRepository(session).get_latest_state(cid)
    ids = {npc.id for npc in state.active_npcs}
    assert "follower_npc" not in ids  # in active_npcs_ids but stored at location B


def test_active_npcs_not_duplicated_when_both():
    # An NPC that is BOTH at the location and in active_npcs_ids appears once.
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Location(id="A", name="Foundry", description=""))
        char = Character(name="Hero", location_id="A")
        session.add(char)
        session.add(DBNPC(id="npc1", name="Gearsmith", location_id="A"))
        session.add(WorldState(current_location_id="A", active_npcs_ids=["npc1"]))
        session.commit()
        session.refresh(char)
        cid = char.id
    with Session(engine) as session:
        state = StateRepository(session).get_latest_state(cid)
    ids = [npc.id for npc in state.active_npcs]
    assert ids.count("npc1") == 1
