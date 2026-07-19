from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union

class Location(BaseModel):
    id: str
    name: str
    description: str
    npcs: Union[List[str], str] = []

class NPC(BaseModel):
    id: str
    name: str
    traits: List[str]
    current_dialogue: Optional[str] = None
    disposition: float = 0.0  # Range -1.0 (Hostile) to 1.0 (Friendly)
    memories: List[Dict[str, str]] = []  # List of { "key": "...", "value": "..." }

class WorldState(BaseModel):
    current_location_id: Optional[str] = None
    active_npcs_ids: Optional[str] = ""
    current_location: Optional[Location] = None
    active_npcs: List[NPC] = []
    global_event: Optional[str] = None
    world_memories: str = ""  # General world history/events

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
    events: Optional[List[Dict[str, Any]]] = None  # List of events triggered by AI

class NarrativeResult(BaseModel):
    narration: str
    state_updates: Optional[Dict[str, Any]] = None
    npcs: Optional[str] = ""
    active_npcs: List[str] = []
    events: Optional[List[Dict[str, Any]]] = None  # Events triggered
