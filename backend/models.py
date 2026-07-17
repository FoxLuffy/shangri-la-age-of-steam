from pydantic import BaseModel
from typing import List, Optional, Dict, Any

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

class PlayerAction(BaseModel):
    action_text: str
    current_location_id: str
    mood: Optional[str] = None
    is_exploration: bool = False

class Prompt(BaseModel):
    system_prompt: str
    user_content: str

class RawResponse(BaseModel):
    text: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    state_updates: Optional[Dict[str, Any]] = None

class NarrativeResult(BaseModel):
    narration: str
    state_updates: Optional[Dict[str, Any]] = None
    active_npcs: List[str]
