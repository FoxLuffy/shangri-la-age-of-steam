from fastapi import FastAPI
from pydantic import BaseModel
from backend.models import PlayerAction, NarrativeResult
from backend.engine import NarrativeEngine
from backend.client import VLLMClient
from backend.models import WorldState, Location
from backend.database import get_session

app = FastAPI()

# Simple mock for demonstration; in production, this would be configured via env vars
mock_client = VLLMClient(api_base="http://localhost:8000/v1")
dummy_state = WorldState(
    current_location=Location(id="1", name="Forest", description="A dark forest", npcs=[]),
    active_npcs=[]
)
engine = NarrativeEngine(dummy_state, mock_client)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/chat", response_model=NarrativeResult)
async def chat(action: PlayerAction):
    result = engine.process_action(action)
    return result
