import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from backend.models import PlayerAction, NarrativeResult, WorldState, Location, NPC
from backend.engine import NarrativeEngine
from backend.client import VLLMClient
from backend.database import create_db_and_tables, get_session, Location as DBLocation, NPC as DBNPC, WorldState as DBWorldState
from backend.repository import StateRepository
from sqlmodel import Session

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure database is initialized and seeded
create_db_and_tables()
with get_session() as session:
    if not session.query(DBWorldState).first():
        loc = DBLocation(
            id="loc_1",
            name="The Rusty Anchor",
            description="A bustling tavern in the dock district.",
            npcs=["npc_1"]
        )
        npc = DBNPC(
            id="npc_1",
            name="Barnaby",
            traits=["brave", "drunk"],
            current_dialogue="Ahoy matey! Pull up a chair and let's have a drink.",
            disposition=0.2,
            memories=[],
            location_id="loc_1"
        )
        state = DBWorldState(
            current_location_id="loc_1",
            active_npcs_ids=["npc_1"],
            global_event=None,
            world_memories=[]
        )
        session.add(loc)
        session.add(npc)
        session.add(state)
        session.commit()

# Configuration from environment variables with defaults
VLLM_API_BASE = os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")

client = VLLMClient(api_base=VLLM_API_BASE)
engine = NarrativeEngine(client)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/chat", response_model=NarrativeResult)
async def chat(action: PlayerAction):
    with get_session() as session:
        result = engine.process_action(action, session)
        return result

@app.get("/state", response_model=WorldState)
async def get_state():
    with get_session() as session:
        repository = StateRepository(session)
        state = repository.get_latest_state()
        if not state:
            raise HTTPException(status_code=404, detail="No world state found.")
        
        pydantic_loc = Location(
            id=state.current_location.id,
            name=state.current_location.name,
            description=state.current_location.description,
            npcs=state.current_location.npcs
        )
        
        pydantic_npcs = []
        for npc in state.active_npcs:
            pydantic_npcs.append(NPC(
                id=npc.id,
                name=npc.name,
                traits=npc.traits,
                current_dialogue=npc.current_dialogue,
                disposition=npc.disposition,
                memories=npc.memories
            ))
            
        return WorldState(
            current_location=pydantic_loc,
            active_npcs=pydantic_npcs,
            global_event=state.global_event,
            world_memories=state.world_memories
        )
