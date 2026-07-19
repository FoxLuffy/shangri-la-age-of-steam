from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.database import engine, WorldState, Location, NPC
from backend.database import get_session
from sqlmodel import Session as SQLModelSession

class StateRepository:
    def __init__(self, session: SQLModelSession):
        self.session = session

    def get_latest_state(self) -> Optional[WorldState]:
        # Get the most recent state
        state = self.session.query(WorldState).order_by(WorldState.id.desc()).first()
        if state:
            # Dynamically fetch and attach current location
            loc = self.session.query(Location).filter(Location.id == state.current_location_id).first()
            object.__setattr__(state, 'current_location', loc)
            # Dynamically fetch and attach active NPCs
            if state.active_npcs_ids:
                npcs = self.session.query(NPC).filter(NPC.id.in_(state.active_npcs_ids)).all()
                object.__setattr__(state, 'active_npcs', npcs)
            else:
                object.__setattr__(state, 'active_npcs', [])
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
                if hasattr(location, key):
                    setattr(location, key, value)
            self.session.commit()
            self.session.refresh(location)
        return location

# Example usage/integration check (internal)
if __name__ == "__main__":
    with get_session() as session:
        repo = StateRepository(session)
        # This is a placeholder for the NarrativeEngine integration
        pass
