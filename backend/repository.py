from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.database import engine, WorldState, Location, NPC
from backend.database import get_session
from sqlmodel import Session as SQLModelSession

class StateRepository:
    def __init__(self, session: SQLModelSession):
        self.session = session

    def get_latest_state(self) -> Optional[WorldState]:
        """
        Retrieves the most recent WorldState from the persistence layer.
        Ensures initial state and location exist if database is empty,
        and hydrates location and active NPC objects.
        """
        state = self.session.query(WorldState).order_by(WorldState.id.desc()).first()
        
        if not state:
            # Seed initial location if empty
            location = self.session.query(Location).first()
            if not location:
                location = Location(
                    id="loc_1",
                    name="The Engine Room",
                    description="A hot, noisy chamber filled with roaring steam pipes and brass gears."
                )
                self.session.add(location)
                self.session.commit()
                self.session.refresh(location)

            state = WorldState(
                current_location_id=location.id,
                active_npcs_ids=[],
                global_event="The Steam Era Begins",
                world_memories=[]
            )
            self.session.add(state)
            self.session.commit()
            self.session.refresh(state)

        # Hydrate current location object onto state
        if hasattr(state, "current_location_id") and state.current_location_id:
            location = self.session.query(Location).filter(Location.id == state.current_location_id).first()
            if location:
                setattr(state, "current_location", location)

        # Hydrate active NPCs onto state
        active_npcs_ids = getattr(state, "active_npcs_ids", []) or []
        if active_npcs_ids:
            npcs = self.session.query(NPC).filter(NPC.id.in_(active_npcs_ids)).all()
            setattr(state, "active_npcs", list(npcs))
        elif hasattr(state, "current_location") and getattr(state.current_location, "npcs", None):
            setattr(state, "active_npcs", list(state.current_location.npcs))
        else:
            setattr(state, "active_npcs", [])

        return state

    def save_state(self, state: WorldState) -> WorldState:
        self.session.add(state)
        self.session.commit()
        self.session.refresh(state)
        return state

    def update_location(self, location_id: str, data: Dict[str, Any]) -> Optional[Location]:
        location = self.session.query(Location).filter(Location.id == location_id).first()
        if location:
            for key, value in data.items():
                if hasattr(location, key) and key != "id":
                    setattr(location, key, value)
            self.session.add(location)
            self.session.commit()
            self.session.refresh(location)
        return location

    def create_or_update_npc(self, npc_data: Dict[str, Any], location_id: str) -> NPC:
        npc_id = npc_data.get("id") or npc_data.get("name", "npc_unknown").lower().replace(" ", "_")
        npc = self.session.query(NPC).filter(NPC.id == npc_id).first()
        if not npc:
            npc = NPC(
                id=npc_id,
                name=npc_data.get("name", "Unknown NPC"),
                traits=npc_data.get("traits", []),
                location_id=location_id
            )
        else:
            if "name" in npc_data:
                npc.name = npc_data["name"]
            if "traits" in npc_data:
                npc.traits = npc_data["traits"]
            if "disposition" in npc_data:
                npc.disposition = npc_data["disposition"]
        self.session.add(npc)
        self.session.commit()
        self.session.refresh(npc)
        return npc

# Example usage/integration check (internal)
if __name__ == "__main__":
    with get_session() as session:
        repo = StateRepository(session)
        pass

