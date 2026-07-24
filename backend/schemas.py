from datetime import datetime
from typing import List

from pydantic import BaseModel


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


from enum import Enum
from typing import Optional


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


class CharacterSchema(BaseModel):
    id: Optional[int]
    name: str


class ItemSchema(BaseModel):
    id: Optional[int]
    name: str
    description: Optional[str] = None
    category: ItemCategory


class RecipeRequirementSchema(BaseModel):
    id: Optional[int]
    recipe_id: int
    item_id: int
    quantity: int


class RecipeSchema(BaseModel):
    id: Optional[int]
    name: str
    description: Optional[str] = None
    result_item_id: int
    result_quantity: int


class InventorySchema(BaseModel):
    id: Optional[int]
    character_id: int
    item_id: int
    quantity: int


class QuestSchema(BaseModel):
    id: Optional[int]
    title: str
    description: Optional[str] = None
    reward_item_id: Optional[int] = None
    reward_quantity: int = 0


class QuestStateSchema(BaseModel):
    id: Optional[int]
    character_id: int
    quest_id: int
    state: QuestStateEnum
