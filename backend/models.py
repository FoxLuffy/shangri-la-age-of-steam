from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlmodel import SQLModel, Field as SQLModelField
from sqlalchemy.orm import declarative_base

# Use SQLAlchemy's declarative_base for the base model
Base = declarative_base()

class Location(BaseModel):
    id: str
    name: str
    description: str
    npcs: Union[List[str], str] = []

class NPC(BaseModel):
    id: str
    name: str
    traits: List[str] = []
    current_dialogue: Optional[str] = None
    disposition: float = 0.0  # Range -1.0 (Hostile) to 1.0 (Friendly)
    memories: List[Dict[str, str]] = []  # List of { "key": "...", "value": "..." }
    faction_id: Optional[str] = None
    
    # Combat
    hp: int = 100
    max_hp: int = 100
    armor: int = 0
    status_effects: List[str] = []
    is_hostile: bool = False

class FactionStandingModel(BaseModel):
    faction_id: str
    faction_name: str
    standing: float

class PropertyModel(BaseModel):
    id: int
    name: str
    description: str
    location_id: str
    owner_id: Optional[int] = None
    price: int
    income_per_tick: int
    property_type: str

class WorkerModel(BaseModel):
    id: int
    npc_id: str
    property_id: int
    role: str
    salary: int

class WorldState(BaseModel):
    current_location_id: Optional[str] = "1"
    active_npcs_ids: Union[List[str], str] = []
    active_automata_ids: List[int] = []
    global_event: Optional[str] = None
    world_memories: Union[List[Dict[str, str]], str] = []
    current_location: Optional[Location] = None
    active_npcs: List[NPC] = []
    inventory: List[Dict[str, Any]] = []
    quests: List[Dict[str, Any]] = []
    factions: List[FactionStandingModel] = []
    active_minigame: Optional[Dict[str, Any]] = None
    is_combat_active: bool = False
    player_stats: Optional[Dict[str, Any]] = None
    properties: List[PropertyModel] = []
    brass_coins: int = 0

class PlayerAction(BaseModel):
    action_text: str
    current_location_id: str = "1"
    mood: Optional[str] = None
    is_exploration: bool = False
    client_id: Optional[str] = None
    character_id: Optional[int] = None

class Prompt(BaseModel):
    system_prompt: str
    user_content: str

class RawResponse(BaseModel):
    text: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    state_updates: Optional[Dict[str, Any]] = None
    events: Optional[List[Dict[str, Any]]] = None

class NarrativeResult(BaseModel):
    narration: str
    state_updates: Optional[Dict[str, Any]] = None
    npcs: Union[List[str], str] = []
    events: Optional[List[Dict[str, Any]]] = None
    is_combat_active: bool = False

# Database Models (SQLModel)

class DBLocation(SQLModel, base=Base):
    __tablename__ = "location"
    id: str = SQLModelField(primary_key=True)
    name: str
    description: str
    npcs: List[str] = SQLModelField(default=[], sa_column=Column(JSON))

class DBNPC(SQLModel, base=Base):
    __tablename__ = "npc"
    id: str = SQLModelField(primary_key=True)
    name: str
    traits: List[str] = SQLModelField(default=[], sa_column=Column(JSON))
    current_dialogue: Optional[str] = None
    disposition: float = SQLModelField(default=0.0)
    memories: List[Dict[str, str]] = SQLModelField(default=[], sa_column=Column(JSON))
    location_id: str = SQLModelField(default="1", index=True, foreign_key="location.id")

class DBWorldState(SQLModel, base=Base):
    __tablename__ = "world_state"
    id: Optional[int] = SQLModelField(default=None, primary_key=True)
    current_location_id: str = SQLModelField(default="1")
    active_npcs_ids: List[str] = SQLModelField(default=[], sa_column=Column(JSON))
    global_event: Optional[str] = None
    world_memories: List[Dict[str, str]] = SQLModelField(default=[], sa_column=Column(JSON))


class DBLedgerEntry(SQLModel, base=Base):
    __tablename__ = "ledger_entry"
    id: Optional[int] = SQLModelField(default=None, primary_key=True)
    timestamp: datetime = SQLModelField(default_factory=datetime.utcnow)
    action: str
    narration: str
    state_updates: Optional[Dict[str, Any]] = SQLModelField(default=None, sa_column=Column(JSON))
    events: Optional[List[Dict[str, Any]]] = SQLModelField(default=None, sa_column=Column(JSON))
    location_id: Optional[str] = None
