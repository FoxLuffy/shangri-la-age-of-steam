import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from backend.models import PlayerAction, NarrativeResult, WorldState, Location
from backend.engine import NarrativeEngine
from backend.client import VLLMClient
from backend.database import get_session

from contextlib import asynccontextmanager
from backend.database_init import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from environment variables with defaults
VLLM_API_BASE = os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")

client = VLLMClient(api_base=VLLM_API_BASE)
engine = NarrativeEngine(client)

# Initial dummy state
dummy_state = WorldState(
    current_location_id="1",
    active_npcs_ids="",
    world_memories=""
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/chat", response_model=NarrativeResult)
async def chat(action: PlayerAction):
    result = engine.process_action(action)
    return result
