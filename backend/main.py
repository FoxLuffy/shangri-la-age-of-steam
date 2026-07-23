import os
import json
import random
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from backend.models import PlayerAction, NarrativeResult, WorldState, Location, NPC
from backend.engine import NarrativeEngine, world_tick
from backend.client import VLLMClient
from backend.database import get_session, engine as db_engine, Location as DBLocation, NPC as DBNPC, WorldState as DBWorldState, Inventory, Recipe, RecipeRequirement, create_db_and_tables, SystemSettings, BugReport, User, UserSession
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

async def simulate_global_market():
    from backend.database import ResourceMarket
    while True:
        await asyncio.sleep(10) # Update market every 10 seconds
        try:
            with get_session() as session:
                markets = session.exec(select(ResourceMarket)).all()
                if not markets:
                    # Initialize
                    for res in ["Brass", "Copper", "Aetherium", "Coal"]:
                        session.add(ResourceMarket(resource_name=res, base_price=10.0, current_price=10.0, volatility=0.1))
                    session.commit()
                    markets = session.exec(select(ResourceMarket)).all()
                
                # Simulate global player actions fluctuating the market
                for m in markets:
                    # Random drift
                    drift = random.uniform(-m.volatility, m.volatility)
                    m.current_price = max(1.0, m.current_price * (1.0 + drift))
                    
                    # Rare global spike (thousands of players buy)
                    if random.random() < 0.05:
                        m.current_price *= 1.5
                        
                    session.add(m)
                session.commit()
                
                # Broadcast to clients
                markets_data = [{"name": m.resource_name, "price": round(m.current_price, 2)} for m in markets]
                await manager.broadcast(json.dumps({"type": "market_sync", "market": markets_data}))
        except Exception as e:
            logger.error(f"Error in market simulation: {e}")

async def simulate_faction_wars():
    from backend.database import FactionStanding, Location, Faction, WorldState
    from sqlalchemy import func
    while True:
        await asyncio.sleep(20) # Check every 20 seconds
        try:
            with get_session() as session:
                # Sum the standing of all characters for each faction
                results = session.exec(select(FactionStanding.faction_id, func.sum(FactionStanding.standing)).group_by(FactionStanding.faction_id)).all()
                for faction_id, total_standing in results:
                    if total_standing > 10.0:
                        # Faction is highly supported globally!
                        # They will launch an offensive and take over a random location
                        target_locs = session.exec(select(Location).where(Location.faction_id != faction_id)).all()
                        if target_locs:
                            target = random.choice(target_locs)
                            target.faction_id = faction_id
                            session.add(target)
                            
                            faction = session.exec(select(Faction).where(Faction.id == faction_id)).first()
                            fact_name = faction.name if faction else faction_id
                            event_msg = f"GLOBAL WAR ALERT: Due to overwhelming player support, the {fact_name} has permanently annexed {target.name}!"
                            
                            # Broadcast to WorldState global_event
                            states = session.exec(select(WorldState)).all()
                            for state in states:
                                state.global_event = event_msg
                                session.add(state)
                                
                            session.commit()
                            
                            # Broadcast immediately
                            await manager.broadcast(json.dumps({"type": "global_event", "event": event_msg}))
                            
                            # Lower standing sum so they don't conquer everything instantly
                            # Reset some players' standings towards this faction
                            standings = session.exec(select(FactionStanding).where(FactionStanding.faction_id == faction_id)).all()
                            for s in standings:
                                s.standing = s.standing * 0.5
                                session.add(s)
                            session.commit()
                            
        except Exception as e:
            logger.error(f"Error in faction war simulation: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB and start the background tasks
    logger.info("Initializing database...")
    create_db_and_tables()
    logger.info("Starting world simulation, market tasks, and faction wars...")
    global world_task
    world_task = asyncio.create_task(world_simulation_loop())
    asyncio.create_task(simulate_global_market())
    asyncio.create_task(simulate_faction_wars())
    
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
    allow_credentials=False,
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
async def get_world_state(character_id: Optional[int] = None):
    with get_session() as session:
        repo = StateRepository(session)
        state = repo.get_latest_state(character_id)
        all_locations = session.exec(select(DBLocation)).all()
        all_npcs = session.exec(select(DBNPC)).all()
        
        active_players = []
        if character_id:
            from backend.database import Character
            current_char = session.get(Character, character_id)
            if current_char and getattr(current_char, "location_id", None):
                same_loc_chars = session.exec(select(Character).where(Character.location_id == current_char.location_id, Character.id != character_id)).all()
            else:
                same_loc_chars = session.exec(select(Character).where(Character.id != character_id)).all()
                
            for c in same_loc_chars:
                active_players.append({
                    "id": c.id,
                    "name": c.name,
                    "character_class": c.character_class,
                    "hp": c.hp,
                    "max_hp": c.max_hp,
                    "steam": c.steam,
                    "max_steam": c.max_steam
                })

        return {
            "state": state,
            "all_locations": all_locations,
            "all_npcs": all_npcs,
            "active_players": active_players
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
        
        if payload.action == "abandon":
            mg.solved = True
            state["message"] = "Minigame abandoned."
        elif payload.action == "reveal_hint":
            state["hint_revealed"] = True
            state["message"] = state.get("hint", "No hint available.")
        elif mg.type == "hack":
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
                    
                    if item.get("state_updates", {}).get("minigame_trigger"):
                        asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps({
                            "type": "trigger_minigame",
                            "minigame_type": item["state_updates"]["minigame_trigger"],
                            "character_id": action.character_id
                        })), loop)

                    for event in item.get("events", []):
                        if isinstance(event, dict) and event.get("type") == "npc_state_change":
                            asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps(event)), loop)

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

@app.post("/modding/upload")
async def upload_mod(file: UploadFile = File(...)):
    """Upload a custom JSON file defining new Locations, NPCs, Items, and Factions."""
    from backend.database import Location, NPC, Item, Faction
    try:
        content = await file.read()
        data = json.loads(content)
        
        with get_session() as session:
            if "factions" in data:
                for f_data in data["factions"]:
                    faction = session.exec(select(Faction).where(Faction.id == f_data["id"])).first()
                    if faction:
                        for k, v in f_data.items():
                            setattr(faction, k, v)
                    else:
                        faction = Faction(**f_data)
                        session.add(faction)
                        
            if "locations" in data:
                for l_data in data["locations"]:
                    loc = session.exec(select(Location).where(Location.id == l_data["id"])).first()
                    if loc:
                        for k, v in l_data.items():
                            setattr(loc, k, v)
                    else:
                        loc = Location(**l_data)
                        session.add(loc)
                        
            if "npcs" in data:
                for n_data in data["npcs"]:
                    npc = session.exec(select(NPC).where(NPC.id == n_data["id"])).first()
                    if npc:
                        for k, v in n_data.items():
                            setattr(npc, k, v)
                    else:
                        npc = NPC(**n_data)
                        session.add(npc)
                        
            if "items" in data:
                for i_data in data["items"]:
                    item = session.exec(select(Item).where(Item.name == i_data["name"])).first()
                    if item:
                        for k, v in i_data.items():
                            setattr(item, k, v)
                    else:
                        item = Item(**i_data)
                        session.add(item)
                        
            session.commit()
            
        return {"status": "success", "message": "Mod data uploaded and integrated successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process mod data: {str(e)}")


@app.get("/workshop/mods")
async def list_workshop_mods():
    """List available mods from the mock registry."""
    registry_path = os.path.join(os.path.dirname(__file__), "workshop_mods", "registry.json")
    if not os.path.exists(registry_path):
        return []
    with open(registry_path, "r") as f:
        return json.load(f)

@app.post("/workshop/mods/{mod_id}/install")
async def install_workshop_mod(mod_id: str):
    """Download and install a mod from the workshop."""
    mod_path = os.path.join(os.path.dirname(__file__), "workshop_mods", f"{mod_id}.json")
    if not os.path.exists(mod_path):
        raise HTTPException(status_code=404, detail="Mod not found")
        
    from backend.database import Location, NPC, Item, Faction
    try:
        with open(mod_path, "r") as f:
            data = json.load(f)
            
        with get_session() as session:
            if "factions" in data:
                for f_data in data["factions"]:
                    faction = session.exec(select(Faction).where(Faction.id == f_data["id"])).first()
                    if faction:
                        for k, v in f_data.items():
                            setattr(faction, k, v)
                    else:
                        faction = Faction(**f_data)
                        session.add(faction)
                        
            if "locations" in data:
                for l_data in data["locations"]:
                    loc = session.exec(select(Location).where(Location.id == l_data["id"])).first()
                    if loc:
                        for k, v in l_data.items():
                            setattr(loc, k, v)
                    else:
                        loc = Location(**l_data)
                        session.add(loc)
                        
            if "npcs" in data:
                for n_data in data["npcs"]:
                    npc = session.exec(select(NPC).where(NPC.id == n_data["id"])).first()
                    if npc:
                        for k, v in n_data.items():
                            setattr(npc, k, v)
                    else:
                        npc = NPC(**n_data)
                        session.add(npc)
                        
            if "items" in data:
                for i_data in data["items"]:
                    item = session.exec(select(Item).where(Item.name == i_data["name"])).first()
                    if item:
                        for k, v in i_data.items():
                            setattr(item, k, v)
                    else:
                        item = Item(**i_data)
                        session.add(item)
                        
            session.commit()
            
        return {"status": "success", "message": f"Mod {mod_id} installed successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to install mod {mod_id}: {str(e)}")


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
    backstory: str = ""
    gear_prompt: str = ""
    show_tutorials: bool = True
    gear: List[Dict[str, Any]] = Field(default_factory=list)
    user_id: Optional[int] = None

class GenerateGearRequest(BaseModel):
    preset: str
    gear_prompt: str

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

@app.post("/characters/generate-gear")
async def generate_gear(req: GenerateGearRequest):
    """Generate starting gear based on player prompt and class."""
    if not req.gear_prompt:
        return {"items": []}
        
    from backend.client import VLLMClient
    import json
    import re
    
    client = VLLMClient()
    prompt = (
        f"You are the game master. The player chose class '{req.preset}' and requested starting gear: '{req.gear_prompt}'. "
        "Grant them 1-3 reasonable starting items. Do not give them overpowered items; powerful items must be acquired in-game. "
        "The category must be one of: Consumables, Equipment, Crafting_Materials, Steam_Tech_Components. "
        "Return ONLY a JSON array of items: [{\"name\": \"Rusty Wrench\", \"description\": \"A heavy wrench.\", \"quantity\": 1, \"category\": \"Equipment\"}]"
    )
    try:
        response = client.generate(prompt=prompt, max_tokens=200, temperature=0.7)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            items = json.loads(json_match.group(0))
            return {"items": items}
        return {"items": []}
    except Exception as e:
        print(f"Failed to generate gear: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate gear")

class ToggleTutorialsRequest(BaseModel):
    show_tutorials: bool

@app.post("/characters/{character_id}/settings/tutorials")
async def toggle_tutorials(character_id: int, req: ToggleTutorialsRequest):
    """Toggle tutorial overlays for a character."""
    from backend.database import Character
    with get_session() as session:
        char = session.exec(select(Character).where(Character.id == character_id)).first()
        if not char:
            raise HTTPException(status_code=404, detail="Character not found")
        char.show_tutorials = req.show_tutorials
        session.add(char)
        session.commit()
        session.refresh(char)
        return {"status": "success", "show_tutorials": char.show_tutorials}

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
    """Create a new character from a preset and their finalized gear."""
    from backend.database import Character, Inventory, Item, ItemCategory
    preset_data = PRESETS.get(req.preset, PRESETS["Wanderer"])
    with get_session() as session:
        char = Character(
            name=req.name,
            character_class=req.preset,
            background=req.backstory if req.backstory.strip() else preset_data["background"],
            stats=preset_data["stats"],
            show_tutorials=req.show_tutorials,
            user_id=req.user_id
        )
        session.add(char)
        session.commit()
        session.refresh(char)
        
        if req.gear and len(req.gear) > 0:
            for item_data in req.gear:
                # Map string category back to Enum safely
                cat_str = item_data.get("category", "Equipment")
                try:
                    category = ItemCategory(cat_str)
                except ValueError:
                    category = ItemCategory.equipment

                item = Item(
                    name=item_data.get("name", "Unknown Item"),
                    description=item_data.get("description", ""),
                    category=category
                )
                session.add(item)
                session.commit()
                session.refresh(item)
                
                inv = Inventory(character_id=char.id, item_id=item.id, quantity=item_data.get("quantity", 1))
                session.add(inv)
            session.commit()
            session.refresh(char)

        # Generate a long overarching quest based on their backstory
        from backend.client import VLLMClient
        from backend.database import Quest, QuestState, QuestStateEnum
        import json
        import re
        
        client = VLLMClient()
        quest_prompt = (
            f"You are the game master. The player character '{char.name}' has the following background: '{char.background}'. "
            "Generate a singular, grand, long-term overarching quest/goal for them in the steampunk world of Shangri-la. "
            "Return ONLY a JSON object: {\"title\": \"Quest Title\", \"description\": \"A long detailed description of the overarching goal.\"}"
        )
        try:
            response = client.generate(prompt=quest_prompt, max_tokens=150, temperature=0.7)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                quest_data = json.loads(json_match.group(0))
                quest = Quest(
                    title=quest_data.get("title", "A Grand Endeavor"),
                    description=quest_data.get("description", "A long journey awaits.")
                )
                session.add(quest)
                session.commit()
                session.refresh(quest)
                
                qs = QuestState(character_id=char.id, quest_id=quest.id, state=QuestStateEnum.active)
                session.add(qs)
                session.commit()
        except Exception as e:
            print(f"Failed to generate long quest: {e}")
            
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

class MarketTradeRequest(BaseModel):
    resource_name: str
    quantity: int
    action: str # "buy" or "sell"

@app.get("/market")
async def get_market():
    from backend.database import ResourceMarket
    with get_session() as session:
        markets = session.exec(select(ResourceMarket)).all()
        return [{"name": m.resource_name, "price": round(m.current_price, 2)} for m in markets]

@app.post("/market/trade")
async def trade_market(character_id: int, req: MarketTradeRequest):
    from backend.database import Character, ResourceMarket, Inventory, Item
    with get_session() as session:
        char = session.exec(select(Character).where(Character.id == character_id)).first()
        market = session.exec(select(ResourceMarket).where(ResourceMarket.resource_name == req.resource_name)).first()
        if not char or not market:
            raise HTTPException(status_code=404, detail="Character or Market not found")
        
        item = session.exec(select(Item).where(Item.name == req.resource_name)).first()
        if not item:
            item = Item(name=req.resource_name, description=f"Raw {req.resource_name}", category="Crafting_Materials")
            session.add(item)
            session.commit()
            session.refresh(item)
            
        inv = session.exec(select(Inventory).where(Inventory.character_id == char.id, Inventory.item_id == item.id)).first()
        
        total_price = int(market.current_price * req.quantity)
        
        if req.action == "buy":
            if char.brass_coins < total_price:
                raise HTTPException(status_code=400, detail="Not enough brass coins")
            char.brass_coins -= total_price
            if not inv:
                inv = Inventory(character_id=char.id, item_id=item.id, quantity=req.quantity)
                session.add(inv)
            else:
                inv.quantity += req.quantity
            market.current_price *= (1.0 + (0.01 * req.quantity))
        elif req.action == "sell":
            if not inv or inv.quantity < req.quantity:
                raise HTTPException(status_code=400, detail="Not enough resources")
            inv.quantity -= req.quantity
            char.brass_coins += total_price
            market.current_price *= (1.0 - (0.01 * req.quantity))
            market.current_price = max(1.0, market.current_price)
            
        session.add(char)
        session.add(market)
        session.commit()
        
        markets = session.exec(select(ResourceMarket)).all()
        markets_data = [{"name": m.resource_name, "price": round(m.current_price, 2)} for m in markets]
        import json
        asyncio.create_task(manager.broadcast(json.dumps({"type": "market_sync", "market": markets_data})))
        
        return {"status": "success", "brass_coins": char.brass_coins, "new_price": round(market.current_price, 2)}


# --- AUTHENTICATION & ACCOUNT MANAGEMENT ---
import hashlib
import secrets
import fastapi
from fastapi import Header
from datetime import datetime

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@app.post("/auth/register")
def register(req: RegisterRequest):
    from backend.database import SystemSettings
    with get_session() as session:
        settings = session.exec(select(SystemSettings)).first()
        if settings and not settings.registration_open:
            raise HTTPException(status_code=403, detail="Registration is currently closed.")

        existing = session.exec(select(User).where(User.username == req.username)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")

        user = User(
            username=req.username,
            password_hash=hash_password(req.password),
            created_at=datetime.utcnow().isoformat() + "Z",
            is_admin=False
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        token = secrets.token_hex(32)
        user_session = UserSession(
            token=token,
            user_id=user.id,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        session.add(user_session)
        session.commit()
        
        return {"status": "success", "token": token, "user_id": user.id}

@app.post("/auth/login")
def login(req: LoginRequest):
    with get_session() as session:
        admin_secret_env = os.environ.get("SAOS_ADMIN_SECRET", "admin")
        if req.username == "admin" and admin_secret_env and req.password == admin_secret_env:
            user = session.exec(select(User).where(User.username == "admin")).first()
            if not user:
                user = User(
                    username="admin",
                    password_hash=hash_password(req.password),
                    created_at=datetime.utcnow().isoformat() + "Z",
                    is_admin=True
                )
                session.add(user)
                session.commit()
                session.refresh(user)
        else:
            user = session.exec(select(User).where(User.username == req.username)).first()
            if not user or user.password_hash != hash_password(req.password):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
        token = secrets.token_hex(32)
        user_session = UserSession(
            token=token,
            user_id=user.id,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        session.add(user_session)
        session.commit()
        
        return {"status": "success", "token": token, "user_id": user.id, "is_admin": user.is_admin}

# --- ADMINISTRATOR API ---
class SettingsUpdate(BaseModel):
    registration_open: bool
    global_system_prompt: Optional[str] = None

def get_admin_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split("Bearer ")[1]
    with get_session() as session:
        user_session = session.exec(select(UserSession).where(UserSession.token == token)).first()
        if not user_session:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = session.get(User, user_session.user_id)
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        return user

@app.get("/admin/settings")
def get_settings(admin: User = fastapi.Depends(get_admin_user)):
    from backend.database import SystemSettings
    with get_session() as session:
        settings = session.exec(select(SystemSettings)).first()
        if not settings:
            settings = SystemSettings()
            session.add(settings)
            session.commit()
            session.refresh(settings)
        return {
            "registration_open": settings.registration_open,
            "global_system_prompt": settings.global_system_prompt
        }

@app.post("/admin/settings")
def update_settings(req: SettingsUpdate, admin: User = fastapi.Depends(get_admin_user)):
    from backend.database import SystemSettings
    with get_session() as session:
        settings = session.exec(select(SystemSettings)).first()
        if not settings:
            settings = SystemSettings()
            session.add(settings)
        settings.registration_open = req.registration_open
        if req.global_system_prompt is not None:
            settings.global_system_prompt = req.global_system_prompt
        session.commit()
        return {"status": "success"}

@app.get("/admin/users")
def get_users(admin: User = fastapi.Depends(get_admin_user)):
    with get_session() as session:
        users = session.exec(select(User)).all()
        return {"users": [{"id": u.id, "username": u.username, "is_admin": u.is_admin} for u in users]}

class NPCUpdate(BaseModel):
    custom_system_prompt: Optional[str] = None

@app.get("/admin/npcs")
def get_npcs(admin: User = fastapi.Depends(get_admin_user)):
    from backend.database import NPC as DBNPC
    with get_session() as session:
        npcs = session.exec(select(DBNPC)).all()
        return {"npcs": [{"id": n.id, "name": n.name, "custom_system_prompt": n.custom_system_prompt} for n in npcs]}

@app.put("/admin/npcs/{npc_id}")
def update_npc(npc_id: str, req: NPCUpdate, admin: User = fastapi.Depends(get_admin_user)):
    from backend.database import NPC as DBNPC
    with get_session() as session:
        npc = session.get(DBNPC, npc_id)
        if not npc:
            raise HTTPException(status_code=404, detail="NPC not found")
        npc.custom_system_prompt = req.custom_system_prompt
        session.commit()
        return {"status": "success"}

@app.delete("/admin/users/{user_id}")
def delete_user(user_id: int, admin: User = fastapi.Depends(get_admin_user)):
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        session.delete(user)
        session.commit()
        return {"status": "success"}

@app.post("/admin/reset-password/{user_id}")
def reset_password(user_id: int, req: RegisterRequest, admin: User = fastapi.Depends(get_admin_user)):
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.password_hash = hash_password(req.password)
        session.add(user)
        session.commit()
        return {"status": "success"}

@app.get("/admin/logs")
def get_logs(admin: User = fastapi.Depends(get_admin_user)):
    from backend.database import LedgerEntry
    with get_session() as session:
        entries = session.exec(select(LedgerEntry).order_by(LedgerEntry.timestamp.desc()).limit(50)).all()
        return {"logs": [{"id": e.id, "character_id": e.character_id, "action": e.action, "narration": e.narration, "timestamp": e.timestamp} for e in entries]}

class BugReportRequest(BaseModel):
    user_id: Optional[int] = None
    text: str
    type: str = "bug"

@app.post("/bugreports")
def submit_bugreport(req: BugReportRequest):
    from backend.database import BugReport
    import logging
    logger = logging.getLogger(__name__)

    with get_session() as session:
        bug = BugReport(
            user_id=req.user_id,
            type=req.type,
            original_text=req.text,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        session.add(bug)
        session.commit()
        session.refresh(bug)
            
        return {"status": "success", "bug_id": bug.id}

@app.get("/admin/bugreports")
def get_bugreports(admin: User = fastapi.Depends(get_admin_user)):
    from backend.database import BugReport
    with get_session() as session:
        bugs = session.exec(select(BugReport).order_by(BugReport.id.desc())).all()
        return {"bugreports": [
            {
                "id": b.id, 
                "user_id": b.user_id, 
                "type": b.type,
                "original_text": b.original_text, 
                "optimized_text": b.optimized_text,
                "status": b.status,
                "created_at": b.created_at
            } for b in bugs
        ]}

@app.delete("/admin/bugreports/{bug_id}")
def delete_bugreport(bug_id: int, admin: User = fastapi.Depends(get_admin_user)):
    from backend.database import BugReport
    with get_session() as session:
        bug = session.get(BugReport, bug_id)
        if not bug:
            raise HTTPException(status_code=404, detail="Bug report not found")
        session.delete(bug)
        session.commit()
        return {"status": "success"}

@app.post("/admin/reports/export_roadmap")
def export_roadmap(admin: User = fastapi.Depends(get_admin_user)):
    from backend.database import BugReport
    from backend.client import VLLMClient
    
    with get_session() as session:
        bugs = session.exec(select(BugReport).order_by(BugReport.id.desc())).all()
        
        if not bugs:
            return {"roadmap": "No reports found to generate roadmap."}

        prompt = "You are a product manager and lead engineer. Below are the community reports (bugs and feature requests). Please analyze all of them, order them by logical priority (critical bugs first, then important features, etc.), and create a clear, step-by-step technical roadmap for development.\n\n"
        for b in bugs:
            prompt += f"[{b.type.upper()}] Report {b.id}:\n{b.original_text}\n\n"
            
        prompt += "Roadmap:\n"
        
        try:
            client = VLLMClient()
            response = client.generate(prompt=prompt, max_tokens=1000, temperature=0.7)
            roadmap_text = ""
            if isinstance(response, dict) and "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                if "text" in choice:
                    roadmap_text = choice["text"]
                elif "message" in choice:
                    roadmap_text = choice["message"].get("content", "")
            elif isinstance(response, dict) and "text" in response:
                roadmap_text = response["text"]
            elif isinstance(response, str):
                roadmap_text = response
                
            return {"roadmap": roadmap_text.strip()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"VLLM processing failed: {str(e)}")

@app.get("/admin/reports/fetch_and_clear")
def fetch_and_clear(admin: User = fastapi.Depends(get_admin_user)):
    # Intended to be called by local AI tools/scripts or admin panel
    from backend.database import BugReport
    with get_session() as session:
        bugs = session.exec(select(BugReport).order_by(BugReport.id.asc())).all()
        data = []
        for b in bugs:
            data.append({
                "id": b.id, 
                "type": b.type, 
                "text": b.original_text, 
                "created_at": b.created_at
            })
            session.delete(b)
        session.commit()
        return {"reports": data}
