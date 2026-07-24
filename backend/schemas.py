from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class SettingsUpdate(BaseModel):
    registration_open: bool
    global_system_prompt: Optional[str] = None

class NPCUpdate(BaseModel):
    custom_system_prompt: Optional[str] = None

class BugReportRequest(BaseModel):
    user_id: Optional[int] = None
    text: str
    type: str = "bug"

class MinigamePlayPayload(BaseModel):
    minigame_id: int
    action: str
    data: Dict[str, Any]

class CharacterCreateRequest(BaseModel):
    name: str
    preset: str = "Wanderer"
    backstory: str = ""
    gear_prompt: str = ""
    show_tutorials: bool = True
    gear: List[Dict[str, Any]] = Field(default_factory=list)
    user_id: Optional[int] = None

class GenerateGearRequest(BaseModel):
    preset: str
    gear_prompt: str

class ToggleTutorialsRequest(BaseModel):
    show_tutorials: bool

class MinigameActionRequest(BaseModel):
    action: str

class MarketTradeRequest(BaseModel):
    resource_name: str
    quantity: int
    action: str  # "buy" or "sell"
