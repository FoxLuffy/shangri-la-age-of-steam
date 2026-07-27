"""A1: combat is location-scoped via CombatSession, so a freshly-created character must
NOT inherit the shared global WorldState.is_combat_active flag.
A2: placeholder enemy names must never instantiate a junk hostile NPC."""

from backend.database import NPC as DBNPC
from backend.database import Character, CombatSession, SQLModel, WorldState, engine
from backend.repository import StateRepository
from sqlmodel import Session, select


def _fresh():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def test_new_character_does_not_inherit_global_combat_flag():
    _fresh()
    with Session(engine) as session:
        # Shared world row has combat flagged active (leftover from another character/session),
        # and there's an active combat session at a DIFFERENT location (loc 9).
        session.add(WorldState(current_location_id="9", is_combat_active=True))
        session.add(CombatSession(location_id="9", is_active=True, turn_order=[], current_turn_index=0))
        # New character spawns at location 1 — no combat session there.
        char = Character(name="Newbie", location_id="1")
        session.add(char)
        session.commit()
        session.refresh(char)

        state = StateRepository(session).get_latest_state(char.id)
        assert state.is_combat_active is False
        assert state.combat_state is None


def test_combat_active_when_session_at_characters_location():
    _fresh()
    with Session(engine) as session:
        session.add(WorldState(current_location_id="1", is_combat_active=False))
        char = Character(name="Fighter", location_id="1")
        session.add(char)
        session.add(CombatSession(location_id="1", is_active=True, turn_order=[], current_turn_index=0))
        session.commit()
        session.refresh(char)

        state = StateRepository(session).get_latest_state(char.id)
        assert state.is_combat_active is True


def test_placeholder_enemy_does_not_create_npc():
    _fresh()
    with Session(engine) as session:
        char = Character(name="Fighter", location_id="1")
        session.add(char)
        session.add(WorldState(current_location_id="1", is_combat_active=False, active_npcs_ids=[]))
        session.commit()
        session.refresh(char)
        cid = char.id

    for junk in ("none", "Unknown Enemy", "", "the enemy"):
        with Session(engine) as session:
            StateRepository(session).apply_combat_update({"is_combat_active": True, "enemy": junk}, cid)
        with Session(engine) as session:
            npcs = session.exec(select(DBNPC)).all()
            assert npcs == [], f"placeholder enemy {junk!r} created an NPC: {[n.name for n in npcs]}"
            # Reset combat session for the next iteration.
            cs = session.exec(select(CombatSession).where(CombatSession.location_id == "1")).first()
            if cs:
                cs.is_active = False
                session.add(cs)
                session.commit()


def test_real_enemy_still_creates_hostile_combatant():
    _fresh()
    with Session(engine) as session:
        char = Character(name="Fighter", location_id="1")
        session.add(char)
        session.add(WorldState(current_location_id="1", is_combat_active=False, active_npcs_ids=[]))
        session.commit()
        session.refresh(char)
        cid = char.id

    with Session(engine) as session:
        StateRepository(session).apply_combat_update({"is_combat_active": True, "enemy": "Brass Sentinel"}, cid)
    with Session(engine) as session:
        enemy = session.exec(select(DBNPC).where(DBNPC.name == "Brass Sentinel")).first()
        assert enemy is not None and enemy.is_hostile is True
