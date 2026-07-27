"""B2: world simulation is turn-gated (no background timers) and never injects phantom NPCs.
The former NPC-to-NPC 'overheard' interactions (which surfaced characters from other
locations) are removed. run_world_turn is the single per-chat-turn entry point."""

from backend.database import (
    Character,
    Faction,
    FactionStanding,
    LedgerEntry,
    Location,
    Property,
    SQLModel,
    WorldState,
    engine,
)
from backend.engine import run_world_turn, tick_faction_wars, tick_market
from sqlmodel import Session, select


def _fresh():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def test_run_world_turn_advances_time_once():
    _fresh()
    with Session(engine) as session:
        session.add(WorldState(current_location_id="1", world_time=5))
        session.commit()

        run_world_turn(session)

        db_state = session.exec(select(WorldState).order_by(WorldState.id.desc())).first()
        assert db_state.world_time == 6  # exactly one tick


def test_run_world_turn_injects_no_npcs_and_no_overheard_events():
    _fresh()
    with Session(engine) as session:
        session.add(WorldState(current_location_id="1", active_npcs_ids=[]))
        session.commit()

        run_world_turn(session)

        db_state = session.exec(select(WorldState).order_by(WorldState.id.desc())).first()
        assert db_state.active_npcs_ids == []  # no phantom NPCs added
        # No "Overheard interaction" ledger entries are produced anymore.
        entries = session.exec(select(LedgerEntry)).all()
        assert not any("Overheard" in (e.action or "") for e in entries)


def test_run_world_turn_pays_property_income():
    _fresh()
    with Session(engine) as session:
        session.add(WorldState(current_location_id="1"))
        char = Character(name="Owner", location_id="1", brass_coins=100)
        session.add(char)
        session.commit()
        session.refresh(char)
        session.add(Property(name="Foundry", description="x", location_id="1", owner_id=char.id, income_per_tick=25))
        session.commit()

        run_world_turn(session)

        session.refresh(char)
        assert char.brass_coins == 125


def test_tick_faction_wars_annexes_when_support_high():
    _fresh()
    with Session(engine) as session:
        session.add(WorldState(current_location_id="1"))
        session.add(Faction(id="iron", name="Iron Syndicate", description="x"))
        # Target location owned by a different faction.
        session.add(Location(id="7", name="Copper Row", description="x", faction_id="guild"))
        c = Character(name="A", location_id="1")
        session.add(c)
        session.commit()
        session.refresh(c)
        session.add(FactionStanding(character_id=c.id, faction_id="iron", standing=15.0))
        session.commit()

        msg = tick_faction_wars(session)

        assert msg and "annexed" in msg
        loc = session.get(Location, "7")
        assert loc.faction_id == "iron"
        db_state = session.exec(select(WorldState).order_by(WorldState.id.desc())).first()
        assert db_state.global_event == msg


def test_tick_market_keeps_prices_valid():
    from backend.database import ResourceMarket

    _fresh()
    with Session(engine) as session:
        session.add(ResourceMarket(resource_name="Coal", base_price=10.0, current_price=10.0, volatility=0.1))
        session.commit()

        tick_market(session)

        m = session.exec(select(ResourceMarket)).first()
        assert m.current_price >= 1.0
