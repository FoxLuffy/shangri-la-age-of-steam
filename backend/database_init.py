import os
from sqlmodel import Session, select
from backend.database import create_db_and_tables, engine, Location, NPC, WorldState

def migrate_db():
    from sqlalchemy import text
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE location ADD COLUMN faction_id VARCHAR;"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE character ADD COLUMN character_class VARCHAR DEFAULT 'Wanderer';"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE character ADD COLUMN background VARCHAR DEFAULT 'A mysterious wanderer with no past.';"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE character ADD COLUMN stats JSON DEFAULT '{\"strength\": 5, \"intellect\": 5, \"charm\": 5}';"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE recipe ADD COLUMN required_faction_id VARCHAR;"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE world_state ADD COLUMN active_automata_ids JSON DEFAULT '[]';"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE playeraction ADD COLUMN mood VARCHAR;"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE playeraction ADD COLUMN is_exploration BOOLEAN DEFAULT 0;"))
        except Exception:
            pass

def seed_data():
    create_db_and_tables()
    migrate_db()
    with Session(engine) as session:
        # Check if locations exist
        existing_loc = session.exec(select(Location)).first()
        if not existing_loc:
            loc1 = Location(
                id="1",
                name="The Rusty Anchor Tavern",
                description="A dim, steam-filled tavern in the low docks district. Thick smog drifts through copper pipes overhead, and sailors speak in hushed tones about the iron syndicate."
            )
            loc2 = Location(
                id="2",
                name="Clockwork Plaza",
                description="A sprawling plaza centered around a massive brass clock tower. Cogwheels turn rhythmically as steam vents discharge with loud huffs. Vendors sell mechanical trinkets."
            )
            loc3 = Location(
                id="3",
                name="The Grand Foundry",
                description="A cavernous industrial warehouse where giant pistons crush glowing iron ore, emitting intense heat and blinding sparks. Automata patrol the walkways."
            )
            loc4 = Location(
                id="4",
                name="The Aetherium Observatory",
                description="High above the smog, this glass-domed structure houses massive brass telescopes aimed at the glowing aether rifts in the sky."
            )
            loc5 = Location(
                id="5",
                name="Undercity Slums",
                description="A labyrinth of cramped, rusted metal shanties beneath the main city grid. It reeks of sulfur and desperation, a haven for smugglers and rogue alchemists."
            )
            session.add_all([loc1, loc2, loc3, loc4, loc5])

            npc1 = NPC(
                id="npc_1",
                name="Barnaby the Chief Engineer",
                traits=["knowledgeable", "cautious", "grumpy"],
                disposition=0.2,
                location_id="3",
                memories=[{"key": "Steam Leaks", "value": "Worried about pressure drops in Sector 4"}]
            )
            npc2 = NPC(
                id="npc_2",
                name="Lady Eleanor Vane",
                traits=["astute", "secretive", "wealthy"],
                disposition=0.0,
                location_id="4",
                memories=[{"key": "Alchemy Experiment", "value": "Seeking refined brass components for her automaton"}]
            )
            npc3 = NPC(
                id="npc_3",
                name="Silas the Smuggler",
                traits=["shrewd", "observant", "cynical"],
                disposition=-0.1,
                location_id="5",
                memories=[{"key": "Dock Patrols", "value": "Keeps a watchful eye out for city enforcers"}]
            )
            npc4 = NPC(
                id="npc_4",
                name="Kaelen Ironhand",
                traits=["brutal", "loyal", "scarred"],
                disposition=-0.5,
                location_id="1",
                memories=[{"key": "Tavern Brawl", "value": "Broke a man's arm over a game of gears last night"}]
            )
            npc5 = NPC(
                id="npc_5",
                name="Madame Vivienne",
                traits=["charming", "manipulative", "elegant"],
                disposition=0.4,
                location_id="2",
                memories=[{"key": "Syndicate Secrets", "value": "Knows which council members take bribes from the undercity"}]
            )
            session.add_all([npc1, npc2, npc3, npc4, npc5])

            world_state = WorldState(
                current_location_id="1",
                active_npcs_ids=["npc_4"],
                global_event="The Great Steam Festival is approaching, filling the city with excitement and restless automatons.",
                world_memories=[{"key": "City News", "value": "The Iron Syndicate has increased tariffs on coal, causing unrest in the undercity."}]
            )
            session.add(world_state)
            
            # Seed ResourceMarket
            from backend.database import ResourceMarket
            res1 = ResourceMarket(resource_name="Coal", base_price=12.0, current_price=12.0, volatility=0.05)
            res2 = ResourceMarket(resource_name="Brass", base_price=45.0, current_price=45.0, volatility=0.1)
            res3 = ResourceMarket(resource_name="Aether", base_price=150.0, current_price=150.0, volatility=0.25)
            session.add_all([res1, res2, res3])
            
            session.commit()
            print("Database seeded with initial locations, NPCs, WorldState, and ResourceMarket.")
        else:
            print("Database already contains data.")

if __name__ == "__main__":
    seed_data()
