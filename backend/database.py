from sqlmodel import Field, Session, SQLModel, create_engine, Relationship
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Text, JSON
from contextlib import contextmanager

# Database setup
sqlite_file_name = "saos.db"
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
    location_id: str = Field(index=True, foreign_key="location.id")
    location: Optional[Location] = Relationship(back_populates="npcs")

class WorldState(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    current_location_id: str
    active_npcs_ids: List[str] = Field(default=[], sa_column=Column(JSON))
    global_event: Optional[str] = None
    world_memories: List[Dict[str, str]] = Field(default=[], sa_column=Column(JSON))

class PlayerAction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    action_text: str
    current_location_id: str

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
