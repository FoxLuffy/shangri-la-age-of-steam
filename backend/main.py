import os
import json
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pydantic import BaseModel
from sqlmodel import Session, select
from backend.models import PlayerAction, NarrativeResult, WorldState, Location, NPC
from backend.engine import NarrativeEngine, world_tick
from backend.client import VLLMClient
from backend.database import get_session, engine as db_engine, Location as DBLocation, NPC as DBNPC, WorldState as DBWorldState, Inventory, Recipe, RecipeRequirement, create_db_and_tables
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
    # Startup: Initialize DB and start the background world tick
    logger.info("Initializing database...")
    create_db_and_tables()
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

class LazyEngine:
    def __init__(self, api_base: str):
        self.api_base = api_base
        self._instance = None

    def process_action(self, action, session):
        if self._instance is None:
            logger.info(f"Lazy-loading VLLMClient from {self.api_base}")
            client = VLLMClient(api_base=self.api_base)
            self._instance = NarrativeEngine(client)
        return self._instance.process_action(action, session)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# This creates a proxy, not the real engine, so no connection happens on import.
engine = LazyEngine(VLLM_API_BASE)

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

class MinigamePlayPayload(BaseModel):
    minigame_id: int
    action: str
    data: Dict[str, Any]

@app.post("/minigame/play")
async def play_minigame(payload: MinigamePlayPayload):
    with get_session() as session:
        from backend.database import Minigame
        mg = session.get(Minigame, payload.minigame_id)
        if not mg or mg.solved:
            raise HTTPException(status_code=400, detail="Minigame not found or already solved.")
            
        import copy
        state = copy.deepcopy(mg.state)
        
        if mg.type == "hack":
            # Simple mastermind/hacking game logic
            if payload.action == "input":
                seq_val = payload.data.get("value")
                state["current_input"].append(seq_val)
                
                # Check if matches
                target = state["sequence"]
                curr = state["current_input"]
                
                if len(curr) == len(target):
                    if curr == target:
                        mg.solved = True
                        state["message"] = "Bypass successful. Access granted."
                    else:
                        state["attempts_left"] -= 1
                        state["current_input"] = []
                        if state["attempts_left"] <= 0:
                            mg.solved = True
                            state["message"] = "Terminal lockout. Hacking failed."
                        else:
                            state["message"] = f"Sequence incorrect. {state['attempts_left']} attempts remaining."
        
        elif mg.type == "lockpick":
            if payload.action == "set_pin":
                pin_idx = payload.data.get("pin_index")
                if 0 <= pin_idx < len(state["pins"]):
                    state["pins"][pin_idx] = True
                    
                if all(state["pins"]):
                    mg.solved = True
                    state["message"] = "Lock picked successfully."
                    
        elif payload.action == "abandon":
            mg.solved = True
            state["message"] = "Minigame abandoned."

        from sqlalchemy.orm.attributes import flag_modified
        mg.state = state
        flag_modified(mg, "state")
        session.add(mg)
        session.commit()
        session.refresh(mg)
        
        return {"status": "success", "solved": mg.solved, "state": mg.state}

@app.post("/chat")
async def chat(action: PlayerAction):
    loop = asyncio.get_running_loop()
    def event_stream():
        with get_session() as session:
            for item in engine.process_action(action, session):
                if isinstance(item, str):
                    yield f"data: {json.dumps({'chunk': item})}\n\n"
                elif isinstance(item, dict):
                    # Broadcast the completed result to all connected websockets
                    # We wrap this inside run_coroutine_threadsafe to run concurrently
                    asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps({
                        "type": "narrative_event",
                        "data": item,
                        "action": action.model_dump()
                    })), loop)
                    yield f"data: {json.dumps({'result': item})}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from client, but keep loop alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/reset")
async def reset_database():
    from backend.database import SQLModel, engine
    # Drop all tables to fully reset
    SQLModel.metadata.drop_all(engine)
    # create_db_and_tables is called inside seed_data, which will recreate them
    seed_data()
    with get_session() as session:
        repo = StateRepository(session)
        state = repo.get_latest_state()
        return {"status": "reset", "state": state}

@app.get("/export")
async def export_save():
    db_path = os.getenv("DATABASE_PATH", "saos.db")
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database file not found.")
    return FileResponse(path=db_path, filename="saos_save.db", media_type="application/octet-stream")

@app.post("/import")
async def import_save(file: UploadFile = File(...)):
    db_path = os.getenv("DATABASE_PATH", "saos.db")
    try:
        with open(db_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Optionally, verify the database or trigger any post-import hooks here.
        # It's important the client calls /state immediately after to refresh data.
        return {"status": "success", "message": "Save state imported successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import save: {str(e)}")

@app.get("/inventory")
async def get_inventory(character_id: int):
    """Retrieve the inventory for a given character."""
    with get_session() as session:
        inventory_items = session.exec(
            select(Inventory).where(Inventory.character_id == character_id)
        ).all()
        return inventory_items

@app.get("/history")
async def get_history(limit: int = 50):
    """Retrieve the world history ledger entries."""
    from backend.database import LedgerEntry
    with get_session() as session:
        entries = session.exec(
            select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(limit)
        ).all()
        return entries

@app.post("/craft")
async def craft_item(character_id: int, recipe_id: int):
    """
    Crafts an item based on a recipe.
    Atomically deducts required materials from character's inventory and adds the new item.
    """
    from backend.database import Recipe, RecipeRequirement, Inventory, WorldState, Location
    with get_session() as session:
        recipe = session.exec(select(Recipe).where(Recipe.id == recipe_id)).first()
        if not recipe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

        # Faction check
        if recipe.required_faction_id:
            ws = session.exec(select(WorldState)).first()
            if ws:
                loc = session.exec(select(Location).where(Location.id == ws.current_location_id)).first()
                if not loc or loc.faction_id != recipe.required_faction_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"This recipe requires the '{recipe.required_faction_id}' faction facilities."
                    )
            
        requirements = session.exec(
            select(RecipeRequirement).where(RecipeRequirement.recipe_id == recipe_id)
        ).all()
        
        if not requirements:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipe has no requirements")
        
        # Check if character has enough materials
        for req in requirements:
            inv_item = session.exec(
                select(Inventory)
                .where(Inventory.character_id == character_id)
                .where(Inventory.item_id == req.item_id)
            ).first()
            
            if not inv_item or inv_item.quantity < req.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Not enough materials for item_id {req.item_id}. Needed: {req.quantity}, Have: {inv_item.quantity if inv_item else 0}"
                )
                
        try:
            # Deduct materials
            for req in requirements:
                inv_item = session.exec(
                    select(Inventory)
                    .where(Inventory.character_id == character_id)
                    .where(Inventory.item_id == req.item_id)
                ).first()
                inv_item.quantity -= req.quantity
                if inv_item.quantity == 0:
                    session.delete(inv_item)
                else:
                    session.add(inv_item)
                
            # Add resulting item to inventory
            result_inv_item = session.exec(
                select(Inventory)
                .where(Inventory.character_id == character_id)
                .where(Inventory.item_id == recipe.result_item_id)
            ).first()
            
            if result_inv_item:
                result_inv_item.quantity += recipe.result_quantity
                session.add(result_inv_item)
            else:
                new_inv_item = Inventory(
                    character_id=character_id, 
                    item_id=recipe.result_item_id, 
                    quantity=recipe.result_quantity
                )
                session.add(new_inv_item)
                
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Crafting transaction failed"
            )
            
        return {
            "message": "Crafting successful",
            "result_item_id": recipe.result_item_id,
            "quantity_added": recipe.result_quantity
        }

@app.get("/quests")
async def get_quests(character_id: int):
    """Retrieve all quests and their states for a given character."""
    with get_session() as session:
        quests = session.exec(
            select(QuestState).where(QuestState.character_id == character_id)
        ).all()
        return quests

@app.get("/market")
async def get_market_prices():
    """Retrieve current market prices for all resources."""
    from backend.database import ResourceMarket
    with get_session() as session:
        markets = session.exec(select(ResourceMarket)).all()
        return markets

@app.get("/automata")
async def get_automata():
    """Retrieve all automata companions."""
    from backend.database import AutomataCompanion
    with get_session() as session:
        automata = session.exec(select(AutomataCompanion)).all()
        return automata

@app.get("/augmentations")
async def get_augmentations(character_id: int = 1):
    """Retrieve augmentations installed on a character."""
    from backend.database import Augmentation
    with get_session() as session:
        augs = session.exec(select(Augmentation).where(Augmentation.character_id == character_id)).all()
        return augs

@app.post("/generate_npc")
async def generate_npc_endpoint(flavor: str = "industrial"):
    """Generate a random procedural NPC for a specific flavor."""
    from backend.npc_generator import generate_procedural_npc
    with get_session() as session:
        npc = generate_procedural_npc(session, location_flavor=flavor)
        return npc

class CharacterCreateRequest(BaseModel):
    name: str
    preset: str = "Wanderer"
    gear_prompt: str = ""

PRESETS = {
    "Aristocrat": {
        "background": "Wealthy heir to a steam-engine fortune.",
        "stats": {"strength": 3, "intellect": 7, "charm": 8}
    },
    "Scrapper": {
        "background": "Grew up in the lower brass-works fighting for scraps.",
        "stats": {"strength": 8, "intellect": 4, "charm": 3}
    },
    "Alchemist": {
        "background": "Former student of the Transmutation Academy.",
        "stats": {"strength": 3, "intellect": 9, "charm": 4}
    },
    "Wanderer": {
        "background": "A mysterious wanderer with no past.",
        "stats": {"strength": 5, "intellect": 5, "charm": 5}
    }
}

@app.get("/characters/{character_id}")
async def get_character(character_id: int):
    """Retrieve character details."""
    from backend.database import Character
    with get_session() as session:
        char = session.exec(select(Character).where(Character.id == character_id)).first()
        if not char:
            raise HTTPException(status_code=404, detail="Character not found")
        return char

@app.post("/characters")
async def create_character(req: CharacterCreateRequest):
    """Create a new character from a preset."""
    from backend.database import Character
    preset_data = PRESETS.get(req.preset, PRESETS["Wanderer"])
    with get_session() as session:
        char = Character(
            name=req.name,
            character_class=req.preset,
            background=preset_data["background"],
            stats=preset_data["stats"]
        )
        session.add(char)
        session.commit()
        session.refresh(char)
        
        if req.gear_prompt:
            from backend.client import VLLMClient
            from backend.database import Inventory, Item
            import json
            client = VLLMClient()
            prompt = (
                f"You are the game master. The player chose class '{req.preset}' and requested starting gear: '{req.gear_prompt}'. "
                "Grant them 1-3 reasonable starting items. Do not give them overpowered items; powerful items must be acquired in-game. "
                "Return ONLY a JSON array of items: [{\"name\": \"Rusty Wrench\", \"description\": \"A heavy wrench.\", \"quantity\": 1, \"type\": \"weapon\"}]"
            )
            try:
                response = client.generate(prompt=prompt, max_tokens=200, temperature=0.7)
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    items = json.loads(json_match.group(0))
                    for item_data in items:
                        item = Item(
                            name=item_data.get("name", "Unknown Item"),
                            description=item_data.get("description", ""),
                            type=item_data.get("type", "misc")
                        )
                        session.add(item)
                        session.commit()
                        session.refresh(item)
                        
                        inv = Inventory(character_id=char.id, item_id=item.id, quantity=item_data.get("quantity", 1))
                        session.add(inv)
                    session.commit()
            except Exception as e:
                print("Failed to generate gear:", e)
        
        return char

class MinigameActionRequest(BaseModel):
    action: str

@app.post("/minigames/start")
async def start_minigame(character_id: int, game_type: str = "gear_lock"):
    """Starts a new sabotage or espionage minigame."""
    from backend.database import Minigame
    with get_session() as session:
        state = {}
        if game_type == "gear_lock":
            state = {"gears": [0, 0, 0], "target": [5, 5, 5]}
        game = Minigame(
            character_id=character_id,
            type=game_type,
            state=state,
            solved=False
        )
        session.add(game)
        session.commit()
        session.refresh(game)
        return game

@app.post("/minigames/{minigame_id}/action")
async def perform_minigame_action(minigame_id: int, req: MinigameActionRequest):
    """Performs an action on a minigame."""
    from backend.database import Minigame
    with get_session() as session:
        game = session.exec(select(Minigame).where(Minigame.id == minigame_id)).first()
        if not game:
            raise HTTPException(status_code=404, detail="Minigame not found")
        
        if req.action == "solve_cheat":
            game.solved = True
        elif game.type == "gear_lock":
            # Just an example of advancing state
            game.state["gears"] = game.state["target"]
            game.solved = True
            
        session.add(game)
        session.commit()
        session.refresh(game)
        return game

@app.post("/airships/acquire")
async def acquire_airship(character_id: int, name: str):
    """Acquires a new airship for a character."""
    from backend.database import Airship
    with get_session() as session:
        ship = Airship(
            character_id=character_id,
            name=name
        )
        session.add(ship)
        session.commit()
        session.refresh(ship)
        return ship

@app.post("/airships/{airship_id}/install_module")
async def install_airship_module(airship_id: int, module_name: str):
    """Installs a module on an airship."""
    from backend.database import Airship
    with get_session() as session:
        ship = session.exec(select(Airship).where(Airship.id == airship_id)).first()
        if not ship:
            raise HTTPException(status_code=404, detail="Airship not found")
        
        modules = ship.modules.copy()
        if module_name not in modules:
            modules.append(module_name)
        ship.modules = modules
        session.add(ship)
        session.commit()
        session.refresh(ship)
        return ship

@app.post("/airships/{airship_id}/fly")
async def fly_airship(airship_id: int, altitude: int, distance: float):
    """Flies the airship to a new altitude and distance, consuming fuel."""
    from backend.database import Airship
    with get_session() as session:
        ship = session.exec(select(Airship).where(Airship.id == airship_id)).first()
        if not ship:
            raise HTTPException(status_code=404, detail="Airship not found")
        
        fuel_cost = (distance * 0.5) + (abs(altitude - ship.current_altitude) * 0.01)
        if ship.fuel_level < fuel_cost:
            raise HTTPException(status_code=400, detail="Not enough fuel")
        
        ship.current_altitude = altitude
        ship.fuel_level -= fuel_cost
        session.add(ship)
        session.commit()
        session.refresh(ship)
        return ship
