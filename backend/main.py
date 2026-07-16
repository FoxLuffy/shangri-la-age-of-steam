from fastapi import FastAPI
from pydantic import BaseModel
from backend.models import PlayerAction, NarrativeResult
from backend.engine import NarrativeEngine
from backend.client import VLLMClient
from backend.models import WorldState, Location

app = FastAPI()

# This would typically be initialized via a dependency injection or global state
# For now, we'll instantiate them here or in a startup event
mock_client = VLLMClient(api_base="http://localhost:8000/v1")
# Note: In a production app, WorldState would be persisted in a DB
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
