from sqlmodel import Field, Session, SQLModel, create_engine, Relationship, select
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.sqlite import JSON

import os

# Database setup
sqlite_file_name = os.getenv("DB_PATH")
if not sqlite_file_name:
    if os.path.exists("/data"):
        sqlite_file_name = "/data/saos.db"
    else:
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
    npcs: str = ""  # Store as comma-separated string or JSON

class NPC(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    traits: List[str] = Field(default=[], sa_column=Column(JSON))
    current_dialogue: Optional[str] = None
    disposition: float = Field(default=0.0)
    memories: List[Dict[str, str]] = Field(default=[], sa_column=Column(JSON))
    location_id: str = Field(index=True, foreign_key="location.id")
    location: Optional[Location] = Relationship()

class WorldState(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    current_location_id: str
    active_npcs_ids: str = Field(default="", sa_column=Column(Text))
    global_event: Optional[str] = None
    world_memories: str = Field(default="", sa_column=Column(Text))

    # Private attributes to store dynamically set values
    _active_npcs: Optional[List[NPC]] = None
    _current_location: Optional[Location] = None

    def __init__(self, **data):
        active_npcs = data.pop("active_npcs", None)
        current_location = data.pop("current_location", None)
        super().__init__(**data)
        if active_npcs is not None:
            self.active_npcs = active_npcs
        if current_location is not None:
            self.current_location = current_location

    @property
    def active_npcs(self) -> List[NPC]:
        if self._active_npcs is not None:
            return self._active_npcs
        from sqlalchemy.orm import object_session
        session = object_session(self)
        if session and self.active_npcs_ids:
            npc_ids = [nid.strip() for nid in self.active_npcs_ids.split(",") if nid.strip()]
            return session.exec(select(NPC).where(NPC.id.in_(npc_ids))).all()
        return []

    @active_npcs.setter
    def active_npcs(self, value: List[NPC]):
        self._active_npcs = value

    @property
    def current_location(self) -> Optional[Location]:
        if self._current_location is not None:
            return self._current_location
        from sqlalchemy.orm import object_session
        session = object_session(self)
        if session and self.current_location_id:
            return session.exec(select(Location).where(Location.id == self.current_location_id)).first()
        return None

    @current_location.setter
    def current_location(self, value: Location):
        self._current_location = value

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
    npcs: str = Field(default="", sa_column=Column(Text))
    active_npcs: List[str] = Field(default=[], sa_column=Column(JSON))
    events: Optional[str] = Field(default=None, sa_column=Column(Text))
