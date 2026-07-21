from sqlmodel import Field, Session, SQLModel, create_engine, Relationship
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Text, JSON
from contextlib import contextmanager
import os
from enum import Enum



sqlite_file_name = os.getenv("DATABASE_PATH", "saos.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session():
    with Session(engine) as session:
        yield session

# Models
class Location(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    description: str
    npcs: List["NPC"] = Relationship(back_populates="location")

class NPC(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    traits: List[str] = Field(default=[], sa_column=Column(JSON))
    current_dialogue: Optional[str] = None
    disposition: float = Field(default=0.0)
    memories: List[Dict[str, str]] = Field(default=[], sa_column=Column(JSON))
    location_id: str = Field(default="1", index=True, foreign_key="location.id")
    location: Optional[Location] = Relationship()

class WorldState(SQLModel, table=True):
    __tablename__ = "world_state"
    id: Optional[int] = Field(default=None, primary_key=True)
    current_location_id: str = Field(default="1")
    active_npcs_ids: List[str] = Field(default=[], sa_column=Column(JSON))
    active_automata_ids: List[int] = Field(default=[], sa_column=Column(JSON))
    global_event: Optional[str] = None
    world_memories: List[Dict[str, str]] = Field(default=[], sa_column=Column(JSON))

class PlayerAction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    action_text: str
    current_location_id: str
    mood: Optional[str] = None
    is_exploration: bool = Field(default=False)

class Prompt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    system_prompt: str
    user_content: str

class RawResponse(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    tool_calls: Optional[str] = Field(default=None, sa_column=Column(JSON))
    state_updates: Optional[str] = Field(default=None, sa_column=Column(JSON))

class NarrativeResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    narration: str
    state_updates: Optional[str] = Field(default=None, sa_column=Column(JSON))
    npcs: List[str] = Field(default=[], sa_column=Column(JSON))
    events: Optional[str] = Field(default=None, sa_column=Column(JSON))

class ItemCategory(str, Enum):
    consumables = "Consumables"
    equipment = "Equipment"
    crafting_materials = "Crafting_Materials"
    steam_tech_components = "Steam_Tech_Components"

class QuestStateEnum(str, Enum):
    available = "Available"
    active = "Active"
    completed = "Completed"
    failed = "Failed"

class Character(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    character_class: Optional[str] = Field(default="Wanderer")
    background: Optional[str] = Field(default="A mysterious wanderer with no past.")
    stats: Dict[str, int] = Field(default={"strength": 5, "intellect": 5, "charm": 5}, sa_column=Column(JSON))

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    category: ItemCategory

class RecipeRequirement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    recipe_id: int = Field(foreign_key="recipe.id")
    item_id: int = Field(foreign_key="item.id")
    quantity: int = Field(default=1)

class Recipe(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    result_item_id: int = Field(foreign_key="item.id")
    result_quantity: int = Field(default=1)

class Inventory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id")
    item_id: int = Field(foreign_key="item.id")
    quantity: int = Field(default=0)

class Quest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    reward_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    reward_quantity: int = Field(default=0)

class QuestState(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id")
    quest_id: int = Field(foreign_key="quest.id")
    state: QuestStateEnum = Field(default=QuestStateEnum.available)

class WorldEvent(SQLModel, table=True):
    __tablename__ = "world_events"
    id: Optional[int] = Field(default=None, primary_key=True)
    location_id: str = Field(index=True)
    event_type: str
    event_text: str
    severity: int = Field(default=1)
    affected_locations: List[str] = Field(default=[], sa_column=Column(JSON))
    faction_impacts: Dict[str, float] = Field(default={}, sa_column=Column(JSON))
    timestamp: str = Field(default="")
    is_active: int = Field(default=1)

class ResourceMarket(SQLModel, table=True):
    __tablename__ = "resource_market"
    id: Optional[int] = Field(default=None, primary_key=True)
    resource_name: str = Field(index=True, unique=True)
    base_price: float = Field(default=10.0)
    current_price: float = Field(default=10.0)
    volatility: float = Field(default=0.1)

class AutomataCompanion(SQLModel, table=True):
    __tablename__ = "automata"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    model_type: str = Field(default="scout")
    core_power: float = Field(default=100.0)
    modules: List[str] = Field(default=[], sa_column=Column(JSON))
    disposition: float = Field(default=1.0)

class Augmentation(SQLModel, table=True):
    __tablename__ = "augmentation"
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id", index=True)
    body_part: str = Field(index=True)
    augmentation_name: str
    stat_bonus: Dict[str, float] = Field(default={}, sa_column=Column(JSON))

