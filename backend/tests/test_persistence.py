import pytest
from sqlmodel import Session, SQLModel, create_engine
from backend.database import Location, NPC, WorldState

def test_persistence():
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        loc = Location(
            id="loc_1",
            name="The Rusty Anchor",
            description="A bustling tavern in the dock district."
        )
        session.add(loc)
        session.commit()

        npc = NPC(
            id="npc_1",
            name="Barnaby",
            traits=["brave", "drunk"],
            location_id="loc_1"
        )
        session.add(npc)
        session.commit()

        state = WorldState(
            current_location_id="loc_1",
            global_event="Festival of Sails"
        )
        session.add(state)
        session.commit()
        session.refresh(state)

        retrieved_loc = session.get(Location, "loc_1")
        assert retrieved_loc.name == "The Rusty Anchor"
        
        retrieved_npc = session.get(NPC, "npc_1")
        assert retrieved_npc.name == "Barnaby"
        assert retrieved_npc.traits == ["brave", "drunk"]

        retrieved_state = session.get(WorldState, state.id)
        assert retrieved_state.current_location_id == "loc_1"
        assert retrieved_state.global_event == "Festival of Sails"
