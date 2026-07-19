import pytest
from sqlmodel import Session, SQLModel
from backend.database import engine, Location, NPC, WorldState, create_db_and_tables

def test_persistence():
    SQLModel.metadata.drop_all(engine)
    create_db_and_tables()
    # Setup
    with Session(engine) as session:
        # Create Location
        loc = Location(
            id="loc_1",
            name="The Rusty Anchor",
            description="A bustling tavern in the dock district."
        )
        session.add(loc)
        session.commit()
        session.refresh(loc)

        # Create NPC
        npc = NPC(
            id="npc_1",
            name="Barnaby",
            traits=["brave", "drunk"],
            location_id="loc_1"
        )
        session.add(npc)
        session.commit()

        # Create WorldState
        state = WorldState(
            current_location_id="loc_1",
            global_event="Festival of Sails"
        )
        session.add(state)
        session.commit()
        session.refresh(state)

        # Verify Queries
        retrieved_loc = session.get(Location, "loc_1")
        assert retrieved_loc.name == "The Rusty Anchor"
        
        retrieved_npc = session.get(NPC, "npc_1")
        assert retrieved_npc.name == "Barnaby"
        assert retrieved_npc.traits == ["brave", "drunk"]
        assert retrieved_npc.location.name == "The Rusty Anchor"

        retrieved_state = session.get(WorldState, state.id)
        assert retrieved_state.current_location_id == "loc_1"
        assert retrieved_state.global_event == "Festival of Sails"
