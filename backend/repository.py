from typing import List, Optional, Dict, Any
from sqlmodel import Session as SQLModelSession, select
from backend.database import engine, Location as DBLocation, NPC as DBNPC, WorldState as DBWorldState
from backend.models import WorldState, Location, NPC
from backend.database_init import seed_data

class StateRepository:
    def __init__(self, session: SQLModelSession):
        self.session = session

    def get_latest_state(self) -> WorldState:
        db_state = self.session.exec(select(DBWorldState).order_by(DBWorldState.id.desc())).first()
        if not db_state:
            seed_data()
            db_state = self.session.exec(select(DBWorldState).order_by(DBWorldState.id.desc())).first()

        loc_id = db_state.current_location_id if db_state else "1"
        db_loc = self.session.get(DBLocation, loc_id)
        if not db_loc:
            current_location = Location(
                id=loc_id,
                name="The Rusty Anchor Tavern",
                description="A dim, steam-filled tavern near the docks.",
                npcs=[]
            )
        else:
            current_location = Location(
                id=db_loc.id,
                name=db_loc.name,
                description=db_loc.description,
                npcs=[npc.id for npc in db_loc.npcs] if hasattr(db_loc, "npcs") and db_loc.npcs and isinstance(db_loc.npcs[0], DBNPC) else (db_loc.npcs or [])
            )

        active_npc_ids = db_state.active_npcs_ids if db_state and db_state.active_npcs_ids else []
        active_npcs: List[NPC] = []
        for npc_id in active_npc_ids:
            db_npc = self.session.get(DBNPC, npc_id)
            if db_npc:
                active_npcs.append(NPC(
                    id=db_npc.id,
                    name=db_npc.name,
                    traits=db_npc.traits or [],
                    current_dialogue=db_npc.current_dialogue,
                    disposition=db_npc.disposition if db_npc.disposition is not None else 0.0,
                    memories=db_npc.memories or []
                ))

        return WorldState(
            current_location_id=current_location.id,
            active_npcs_ids=active_npc_ids,
            global_event=db_state.global_event if db_state else None,
            world_memories=db_state.world_memories if db_state else [],
            current_location=current_location,
            active_npcs=active_npcs
        )

    def save_state(self, state: WorldState) -> WorldState:
        db_state = DBWorldState(
            current_location_id=state.current_location_id,
            active_npcs_ids=state.active_npcs_ids if isinstance(state.active_npcs_ids, list) else [],
            global_event=state.global_event,
            world_memories=state.world_memories if isinstance(state.world_memories, list) else []
        )
        self.session.add(db_state)
        self.session.commit()
        self.session.refresh(db_state)
        return state

    def update_location(self, location_id: str, data: Dict[str, Any]) -> Optional[DBLocation]:
        location = self.session.get(DBLocation, location_id)
        if location:
            for key, value in data.items():
                if hasattr(location, key) and key != "id":
                    setattr(location, key, value)
            self.session.add(location)
            self.session.commit()
            self.session.refresh(location)
        return location

    def update_npc(self, npc_id: str, disposition_delta: Optional[float] = None, new_memory: Optional[Dict[str, str]] = None) -> Optional[DBNPC]:
        npc = self.session.get(DBNPC, npc_id)
        if npc:
            if disposition_delta is not None:
                npc.disposition = max(-1.0, min(1.0, npc.disposition + disposition_delta))
            if new_memory:
                memories = list(npc.memories or [])
                memories.append(new_memory)
                npc.memories = memories
            self.session.commit()
            self.session.refresh(npc)
        return npc

    def create_or_update_npc(self, npc_data: Dict[str, Any], location_id: str) -> DBNPC:
        npc_id = npc_data.get("id") or npc_data.get("name", "npc_unknown").lower().replace(" ", "_")
        npc = self.session.get(DBNPC, npc_id)
        if not npc:
            npc = DBNPC(
                id=npc_id,
                name=npc_data.get("name", "Unknown NPC"),
                traits=npc_data.get("traits", []),
                disposition=npc_data.get("disposition", 0.0),
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

if __name__ == "__main__":
    with get_session() as session:
        repo = StateRepository(session)
        pass
