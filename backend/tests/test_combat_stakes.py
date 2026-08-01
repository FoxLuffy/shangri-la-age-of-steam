"""A3: combat has real mechanical stakes. Damage is resolved deterministically from stats
each exchange (the model's hp_change is ignored while combat is active), enemies actually
lose HP and can be killed, and the fight still ends only when the model sets
is_combat_active=false."""

from backend.database import NPC as DBNPC
from backend.database import Bounty, Character, CombatSession, SQLModel, WorldState, engine
from backend.repository import StateRepository
from sqlmodel import Session, select


def _fresh():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_fight():
    _fresh()
    with Session(engine) as session:
        char = Character(name="Fighter", location_id="1", hp=100, max_hp=100, brass_coins=0)
        char.stats = {"strength": 6, "intellect": 5, "charm": 5, "speed": 5}
        session.add(char)
        session.add(WorldState(current_location_id="1", is_combat_active=False, active_npcs_ids=[]))
        session.commit()
        session.refresh(char)
        return char.id


def test_exchange_deals_damage_despite_llm_zero():
    cid = _seed_fight()
    with Session(engine) as session:
        # Model narrates a fight but emits hp_change 0 for everyone.
        StateRepository(session).apply_combat_update(
            {
                "is_combat_active": True,
                "enemy": "Brass Sentinel",
                "player_updates": {"hp_change": 0},
                "npc_updates": [],
            },
            cid,
        )
    with Session(engine) as session:
        char = session.get(Character, cid)
        enemy = session.exec(select(DBNPC).where(DBNPC.name == "Brass Sentinel")).first()
        assert enemy is not None
        assert enemy.hp < enemy.max_hp  # enemy took deterministic damage
        assert char.hp < 100  # enemy retaliated (it survived the first blow)


def test_repeated_exchanges_kill_the_enemy_and_complete_bounty():
    cid = _seed_fight()
    with Session(engine) as session:
        char = session.get(Character, cid)
        b = Bounty(title="Bounty: Sentinel", description="d", target_npc_type="Sentinel", reward_coins=100, status="active")
        session.add(b)
        session.commit()
        session.refresh(b)
        char.active_bounties = [b.id]
        session.add(char)
        session.commit()
        bid = b.id

    for _ in range(15):
        with Session(engine) as session:
            enemy = session.exec(select(DBNPC).where(DBNPC.name == "Brass Sentinel")).first()
            if enemy and enemy.hp == 0:
                break
            StateRepository(session).apply_combat_update(
                {"is_combat_active": True, "enemy": "Brass Sentinel"}, cid
            )

    with Session(engine) as session:
        enemy = session.exec(select(DBNPC).where(DBNPC.name == "Brass Sentinel")).first()
        char = session.get(Character, cid)
        assert enemy.hp == 0  # enemy defeated by deterministic damage
        assert session.get(Bounty, bid).status == "completed"  # bounty auto-completed on kill
        assert char.brass_coins == 100  # reward paid


def test_server_does_not_auto_end_combat_on_kill():
    cid = _seed_fight()
    for _ in range(15):
        with Session(engine) as session:
            enemy = session.exec(select(DBNPC).where(DBNPC.name == "Brass Sentinel")).first()
            if enemy and enemy.hp == 0:
                break
            StateRepository(session).apply_combat_update(
                {"is_combat_active": True, "enemy": "Brass Sentinel"}, cid
            )
    # Enemy dead, but combat is still active — ending is model-driven.
    with Session(engine) as session:
        db_state = session.exec(select(WorldState).order_by(WorldState.id.desc())).first()
        assert db_state.is_combat_active is True
        cs = session.exec(select(CombatSession).where(CombatSession.location_id == "1")).first()
        assert cs.is_active is True

    # The model ends the fight.
    with Session(engine) as session:
        StateRepository(session).apply_combat_update({"is_combat_active": False}, cid)
    with Session(engine) as session:
        db_state = session.exec(select(WorldState).order_by(WorldState.id.desc())).first()
        assert db_state.is_combat_active is False
