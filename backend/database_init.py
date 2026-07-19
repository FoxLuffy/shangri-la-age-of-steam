from sqlmodel import SQLModel, Session, select
from backend.database import engine, Location, NPC, WorldState, create_db_and_tables

def init_db():
    print("Creating tables if they do not exist...")
    create_db_and_tables()

    with Session(engine) as session:
        # Check if database is already seeded
        existing_loc = session.exec(select(Location)).first()
        if existing_loc is not None:
            print("Database already contains data. Skipping seeding.")
            return

        print("Seeding database...")
        # Create Location
        loc = Location(
            id="loc_1",
            name="The Rusty Anchor",
            description="A bustling tavern in the dock district.",
            npcs="npc_1"
        )
        session.add(loc)

        # Create NPC
        npc = NPC(
            id="npc_1",
            name="Barnaby",
            traits=["brave", "drunk"],
            disposition=0.0,
            memories=[],
            location_id="loc_1"
        )
        session.add(npc)

        # Create WorldState
        state = WorldState(
            current_location_id="loc_1",
            active_npcs_ids="npc_1",
            global_event="Festival of Sails",
            world_memories=""
        )
        session.add(state)

        session.commit()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
