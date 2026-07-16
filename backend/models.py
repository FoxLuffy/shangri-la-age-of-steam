from pydantic import BaseModel
from typing import List, Optional

class Location(BaseModel):
    id: str
    name: str
    description: str
    npcs: List[str]

class NPC(BaseModel):
    id: str
    name: str
    traits: List[str]
    current_dialogue: Optional[str] = None

class WorldState(BaseModel):
    current_location: Location
    active_npcs: List[NPC]
    global_event: Optional[str] = None
