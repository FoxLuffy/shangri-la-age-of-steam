import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from backend.models import PlayerAction, NarrativeResult, WorldState, Location, NPC
from backend.engine import NarrativeEngine, world_tick
from backend.client import VLLMClient
from backend.database import get_session, engine as db_engine, Location as DBLocation, NPC as DBNPC, WorldState as DBWorldState
from backend.repository import StateRepository
from backend.database_init import seed_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Background task reference
world_task = None

async def world_simulation_loop():
    while True:
        try:
            await world_tick()
            await asyncio.sleep(60) # Tick every 60 seconds
        except asyncio.CancelledError:
            logger.info("World simulation loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in world simulation loop: {e}")
            await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background world tick
    logger.info("Starting world simulation background task...")
    global world_task
    world_task = asyncio.create_task(world_simulation_loop())
    
    yield
    
    # Shutdown: Cancel the background task
    logger.info("Stopping world simulation background task...")
    if world_task:
        world_task.cancel()
        try:
            await world_task
        except asyncio.CancelledError:
            pass

app = FastAPI(title="Shangri-la: Age of Steam API", lifespan=lifespan)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VLLM_API_BASE = os.getenv("VLLM_SERVER_URL") or os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")
client = VLLMClient(api_base=VLLM_API_BASE)
mock_client = client
engine = NarrativeEngine(client)

dummy_state = WorldState(
    current_location_id="1",
    active_npcs_ids=[],
    world_memories=[]
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "vllm_api": VLLM_API_BASE}

@app.get("/state")
async def get_world_state():
    with get_session() as session:
        repo = StateRepository(session)
        state = repo.get_latest_state()
        all_locations = session.exec(select(DBLocation)).all()
        all_npcs = session.exec(select(DBNPC)).all()
        return {
            "state": state,
            "all_locations": all_locations,
            "all_npcs": all_npcs
        }

@app.post("/chat", response_model=NarrativeResult)
async def chat(action: PlayerAction):
    with get_session() as session:
        result = engine.process_action(action, session)
        return result

@app.post("/reset")
async def reset_database():
    seed_data()
    with get_session() as session:
        repo = StateRepository(session)
        state = repo.get_latest_state()
        return {"status": "reset", "state": state}
