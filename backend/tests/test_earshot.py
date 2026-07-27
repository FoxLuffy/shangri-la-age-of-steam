"""Earshot P1: NPCs the player is actively engaged with are flagged in_earshot; naming a
present NPC brings them into earshot; leaving the location clears the scene set; and the
narrative prompt splits engaged (in earshot) from merely nearby NPCs."""

from backend.database import NPC as DBNPC
from backend.database import Character, SQLModel, WorldState, engine
from backend.models import NPC as NPCModel
from backend.models import PlayerAction
from backend.models import WorldState as WSModel
from backend.prompt_utils import build_narrative_prompt
from backend.repository import StateRepository
from sqlmodel import Session, select


def _fresh():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def test_scene_npc_is_in_earshot_location_npc_is_not():
    _fresh()
    with Session(engine) as session:
        char = Character(name="Ada", location_id="1")
        session.add(char)
        session.add(DBNPC(id="silas", name="Silas", location_id="1"))
        session.add(DBNPC(id="mara", name="Mara", location_id="1"))
        # Only Silas is in the active scene set.
        session.add(WorldState(current_location_id="1", active_npcs_ids=["silas"]))
        session.commit()
        session.refresh(char)

        state = StateRepository(session).get_latest_state(char.id)
        by_name = {n.name: n for n in state.active_npcs}
        assert by_name["Silas"].in_earshot is True
        assert by_name["Mara"].in_earshot is False


def test_naming_a_present_npc_brings_them_into_earshot():
    _fresh()
    with Session(engine) as session:
        char = Character(name="Ada", location_id="1")
        session.add(char)
        session.add(DBNPC(id="mara", name="Mara the Fixer", location_id="1"))
        session.add(WorldState(current_location_id="1", active_npcs_ids=[]))
        session.commit()
        session.refresh(char)

        repo = StateRepository(session)
        state = repo.get_latest_state(char.id)
        engaged = repo.engage_named_npcs("I ask Mara about the missing cargo", state)

        assert "mara" in engaged
        assert next(n for n in state.active_npcs if n.id == "mara").in_earshot is True
        db_state = session.exec(select(WorldState).order_by(WorldState.id.desc())).first()
        assert "mara" in db_state.active_npcs_ids


def test_focus_shift_moves_engagement_to_newly_named_npc():
    _fresh()
    with Session(engine) as session:
        char = Character(name="Ada", location_id="1")
        session.add(char)
        session.add(DBNPC(id="silas", name="Silas", location_id="1"))
        session.add(DBNPC(id="mara", name="Mara", location_id="1"))
        # Silas is currently engaged.
        session.add(WorldState(current_location_id="1", active_npcs_ids=["silas"]))
        session.commit()
        session.refresh(char)

        repo = StateRepository(session)
        state = repo.get_latest_state(char.id)
        # Player turns to Mara — focus shifts to her, Silas drops to nearby.
        repo.engage_named_npcs("I turn to Mara and ask about the docks", state)

        by_name = {n.name: n for n in state.active_npcs}
        assert by_name["Mara"].in_earshot is True
        assert by_name["Silas"].in_earshot is False
        db_state = session.exec(select(WorldState).order_by(WorldState.id.desc())).first()
        assert db_state.active_npcs_ids == ["mara"]


def test_prompt_splits_engaged_from_nearby():
    engaged = NPCModel(id="silas", name="Silas", in_earshot=True)
    nearby = NPCModel(id="mara", name="Mara", in_earshot=False)
    state = WSModel(active_npcs=[engaged, nearby])
    text = build_narrative_prompt(state, PlayerAction(action_text="look around"))
    engaged_hdr = text.index("In earshot (actively engaged")
    nearby_hdr = text.index("Nearby (present but not engaged")
    # Silas is listed under the engaged header; Mara under the nearby header.
    assert engaged_hdr < text.index("Silas") < nearby_hdr < text.index("Mara")
