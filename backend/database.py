import os
from contextlib import contextmanager
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine

sqlite_file_name = os.getenv("DATABASE_PATH", "saos.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=False)

from sqlalchemy import text


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            session.execute(text("ALTER TABLE character ADD COLUMN location_id VARCHAR"))
            session.commit()
    except Exception:
        pass


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session


# Models
class Location(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    description: str
    faction_id: Optional[str] = None
    npcs: List["NPC"] = Relationship(back_populates="location")


class NPC(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    traits: List[str] = Field(default=[], sa_column=Column(JSON))
    current_dialogue: Optional[str] = None
    disposition: float = Field(default=0.0)
    memories: List[Dict[str, str]] = Field(default=[], sa_column=Column(JSON))
    location_id: str = Field(default="1", index=True, foreign_key="location.id")
    faction_id: Optional[str] = Field(default=None, foreign_key="faction.id")
    location: Optional[Location] = Relationship()
    custom_system_prompt: Optional[str] = Field(default=None)

    # Combat Stats
    speed: int = Field(default=5)
    hp: int = Field(default=100)
    max_hp: int = Field(default=100)
    armor: int = Field(default=0)
    status_effects: List[str] = Field(default=[], sa_column=Column(JSON))
    is_hostile: bool = Field(default=False)


class WorldState(SQLModel, table=True):
    __tablename__ = "world_state"
    id: Optional[int] = Field(default=None, primary_key=True)
    current_location_id: str = Field(default="1")
    active_npcs_ids: List[str] = Field(default=[], sa_column=Column(JSON))
    active_automata_ids: List[int] = Field(default=[], sa_column=Column(JSON))
    global_event: Optional[str] = None
    world_memories: List[Dict[str, str]] = Field(default=[], sa_column=Column(JSON))
    is_combat_active: bool = Field(default=False)


class PlayerAction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    action_text: str
    current_location_id: str
    timestamp: str
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
    state_updates: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    npcs: List[str] = Field(default=[], sa_column=Column(JSON))
    events: List[str] = Field(default=[], sa_column=Column(JSON))


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


class Faction(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    description: str


class FactionStanding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id", index=True)
    faction_id: str = Field(foreign_key="faction.id", index=True)
    standing: float = Field(default=0.0)  # -1.0 (hated) to 1.0 (revered)


class User(SQLModel, table=True):
    __tablename__ = "user_account"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    is_admin: bool = Field(default=False)
    created_at: str = Field(default="")


class UserSession(SQLModel, table=True):
    __tablename__ = "user_session"
    token: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="user_account.id", index=True)
    created_at: str = Field(default="")
    expires_at: str = Field(default="")


class Character(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user_account.id", index=True)
    name: str
    character_class: Optional[str] = Field(default="Wanderer")
    background: Optional[str] = Field(default="A mysterious wanderer with no past.")
    stats: Dict[str, int] = Field(
        default={"strength": 5, "intellect": 5, "charm": 5, "speed": 5}, sa_column=Column(JSON)
    )

    # Combat Stats
    hp: int = Field(default=100)
    max_hp: int = Field(default=100)
    armor: int = Field(default=5)
    steam: int = Field(default=100)
    max_steam: int = Field(default=100)
    status_effects: List[str] = Field(default=[], sa_column=Column(JSON))
    # Empire & Wealth
    brass_coins: int = Field(default=100)
    # Settings
    show_tutorials: bool = Field(default=True)
    location_id: str = Field(default="1", index=True)


class SystemSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    registration_open: bool = Field(default=True)
    global_system_prompt: Optional[str] = Field(default=None)


class BugReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user_account.id")
    type: str = Field(default="bug")
    original_text: str
    optimized_text: Optional[str] = Field(default=None)
    created_at: str
    status: str = Field(default="open")


class Property(SQLModel, table=True):
    __tablename__ = "property"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    location_id: str = Field(foreign_key="location.id", index=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="character.id")
    price: int = Field(default=1000)
    income_per_tick: int = Field(default=10)
    property_type: str = Field(default="factory")


class Worker(SQLModel, table=True):
    __tablename__ = "worker"
    id: Optional[int] = Field(default=None, primary_key=True)
    npc_id: str = Field(foreign_key="npc.id", index=True)
    property_id: int = Field(foreign_key="property.id", index=True)
    role: str = Field(default="laborer")
    salary: int = Field(default=5)


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
    required_faction_id: Optional[str] = None


class Inventory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id")
    item_id: int = Field(foreign_key="item.id")
    quantity: int = Field(default=0)
    durability: Optional[int] = Field(default=100)


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


class Minigame(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id", index=True)
    type: str = Field(index=True)
    state: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    solved: bool = Field(default=False)


class Airship(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id", index=True)
    name: str
    hull_integrity: float = Field(default=100.0)
    fuel_level: float = Field(default=100.0)
    current_altitude: int = Field(default=0)
    modules: List[str] = Field(default=[], sa_column=Column(JSON))


class LedgerEntry(SQLModel, table=True):
    __tablename__ = "ledger_entry"
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: Optional[int] = Field(default=None, foreign_key="character.id", index=True)
    timestamp: str = Field(default="")
    action: str
    narration: str
    state_updates: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    events: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    location_id: Optional[str] = None


class CombatSession(SQLModel, table=True):
    __tablename__ = "combat_session"
    id: Optional[int] = Field(default=None, primary_key=True)
    location_id: str = Field(index=True, unique=True)
    is_active: bool = Field(default=False)
    turn_order: List[Dict[str, Any]] = Field(
        default=[], sa_column=Column(JSON)
    )  # [{"id": "...", "type": "player|npc", "speed": 10, "name": "..."}]
    current_turn_index: int = Field(default=0)
