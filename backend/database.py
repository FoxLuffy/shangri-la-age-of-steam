from sqlmodel import Field, Session, SQLModel, create_engine, Relationship
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Text

# Database setup
sqlite_file_name = "saos.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

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
    traits: str = Field(default="", sa_column=Column(Text))
    current_dialogue: Optional[str] = None
    location_id: str = Field(index=True, foreign_key="location.id")
    location: Location = Relationship(back_populates="npcs")

class WorldState(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    current_location_id: str
    active_npcs_ids: str = Field(default="", sa_column=Column(Text))
    global_event: Optional[str] = None

# Narrative results and prompts
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
    tool_calls: Optional[str] = Field(default=None, sa_column=Column(Text))
    state_updates: Optional[str] = Field(default=None, sa_column=Column(Text))

class NarrativeResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    narration: str
    state_updates: Optional[str] = Field(default=None, sa_column=Column(Text))
    active_npcs: str = Field(default="", sa_column=Column(Text))
