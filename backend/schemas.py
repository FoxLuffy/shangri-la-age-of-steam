from pydantic import BaseModel
from typing import List
from datetime import datetime

class WorldEventBase(BaseModel):
    location_id: int
    event_text: str
    involved_npc_ids: List[int]

class WorldEventCreate(WorldEventBase):
    pass

class WorldEvent(WorldEventBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True
