import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.database import DBWorldState, DBWorldEvent
from backend.models import WorldState, WorldEvent

logger = logging.getLogger(__name__)

class WorldEventManager:
    def __init__(self, session: Session):
        self.session = session

    def get_active_events(self) -> List[WorldEvent]:
        """Fetch all currently active world events."""
        statement = select(DBWorldEvent).where(DBWorldEvent.is_active == 1)
        db_events = self.session.exec(statement).all()
        return [WorldEvent(**e.dict()) for e in db_events]

    def trigger_event(self, 
                       location_id: str, 
                       event_type: str, 
                       event_text: str, 
                       severity: int = 1,
                       affected_locations: Optional[List[str]] = None,
                       faction_impacts: Optional[Dict[str, float]] = None) -> WorldEvent:
        """Trigger a new world event and save it to the database."""
        new_event = DBWorldEvent(
            location_id=location_id,
            event_type=event_type,
            event_text=event_text,
            severity=severity,
            affected_locations=affected_locations or [location_id],
            faction_impacts=faction_impacts or {},
            is_active=1
        )
        self.session.add(new_event)
        self.session.commit()
        self.session.refresh(new_event)
        return WorldEvent(**new_event.dict())

    def get_events_for_location(self, location_id: str) -> List[WorldEvent]:
        """Fetch events that affect a specific location."""
        statement = select(DBWorldEvent).where(DBWorldEvent.is_active == 1)
        db_events = self.session.exec(statement).all()
        return [WorldEvent(**e.dict()) for e in db_events if location_id in e.affected_locations]

    def apply_event_impacts(self, active_events: List[WorldEvent], 
                             npc_ids: List[str], 
                             faction_map: Dict[str, List[str]]) -> Dict[str, float]:
        """
        Calculate and return disposition deltas for NPCs based on active events.
        faction_map: { "faction_id": ["npc_id_1", "npc_id_2"] }
        Returns: { "npc_id": total_delta }
        """
        deltas = {}
        for event in active_events:
            for faction_id, delta in event.faction_impacts.items():
                if faction_id in faction_map:
                    for npc_id in faction_map[faction_id]:
                        deltas[npc_id] = deltas.get(npc_id, 0.0) + delta
        return deltas
