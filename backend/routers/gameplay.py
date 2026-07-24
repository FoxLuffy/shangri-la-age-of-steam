import asyncio
import json
import os
import re
from typing import Optional

from backend.client import VLLMClient
from backend.database import NPC as DBNPC
from backend.database import (
    Airship,
    Character,
    Inventory,
    ItemCategory,
    Minigame,
    Quest,
    QuestState,
    QuestStateEnum,
    get_session,
)
from backend.database import Item as DBItem
from backend.database import Location as DBLocation
from backend.engine import NarrativeEngine
from backend.models import PlayerAction
from backend.repository import StateRepository
from backend.schemas import (
    CharacterCreateRequest,
    GenerateGearRequest,
    MinigameActionRequest,
    MinigamePlayPayload,
    ToggleTutorialsRequest,
)
from backend.websocket import manager
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlmodel import select

router = APIRouter()

VLLM_API_BASE = os.getenv("VLLM_SERVER_URL") or os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")

class LazyEngine:
    def __init__(self, api_base: str):
        self.api_base = api_base
        self._instance = None

    def process_action(self, action, session):
        if self._instance is None:
            client = VLLMClient(api_base=self.api_base)
            self._instance = NarrativeEngine(client)
        return self._instance.process_action(action, session)

engine = LazyEngine(VLLM_API_BASE)

PRESETS = {
    "Aristocrat": {
        "background": "Wealthy heir to a steam-engine fortune.",
        "stats": {"strength": 3, "intellect": 7, "charm": 8},
    },
    "Scrapper": {
        "background": "Grew up in the lower brass-works fighting for scraps.",
        "stats": {"strength": 8, "intellect": 4, "charm": 3},
    },
    "Alchemist": {
        "background": "Former student of the Transmutation Academy.",
        "stats": {"strength": 3, "intellect": 9, "charm": 4},
    },
    "Wanderer": {
        "background": "A mysterious wanderer with no past.",
        "stats": {"strength": 5, "intellect": 5, "charm": 5},
    },
}

@router.get("/state")
async def get_world_state(character_id: Optional[int] = None):
    with get_session() as session:
        repo = StateRepository(session)
        state = repo.get_latest_state(character_id)
        all_locations = session.exec(select(DBLocation)).all()
        all_npcs = session.exec(select(DBNPC)).all()

        active_players = []
        if character_id:
            current_char = session.get(Character, character_id)
            if current_char and getattr(current_char, "location_id", None):
                same_loc_chars = session.exec(
                    select(Character).where(
                        Character.location_id == current_char.location_id, Character.id != character_id
                    )
                ).all()
            else:
                same_loc_chars = session.exec(select(Character).where(Character.id != character_id)).all()

            for c in same_loc_chars:
                active_players.append(
                    {
                        "id": c.id,
                        "name": c.name,
                        "character_class": c.character_class,
                        "hp": c.hp,
                        "max_hp": c.max_hp,
                        "steam": c.steam,
                        "max_steam": c.max_steam,
                    }
                )

        return {"state": state, "all_locations": all_locations, "all_npcs": all_npcs, "active_players": active_players}

@router.get("/sessions/{user_id}")
async def get_user_sessions(user_id: int):
    with get_session() as session:
        repo = StateRepository(session)
        return repo.get_sessions(user_id)

@router.post("/minigame/play")
async def play_minigame(payload: MinigamePlayPayload):
    with get_session() as session:
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
            # Mastermind/hacking game logic
            if payload.action == "clear_input":
                state["current_input"] = []
            elif payload.action == "input":
                seq_val = payload.data.get("value")
                state["current_input"].append(seq_val)

                # Check if we have a full guess
                target = state["sequence"]
                curr = state["current_input"]

                if len(curr) == len(target):
                    if curr == target:
                        state["guesses"].append({"guess": curr, "correct_pos": len(target), "correct_char": 0})
                        mg.solved = True
                        state["message"] = "Bypass successful. Access granted."
                    else:
                        state["attempts_left"] -= 1

                        correct_pos = sum(1 for c, t in zip(curr, target) if c == t)
                        target_counts = {}
                        for t in target:
                            target_counts[t] = target_counts.get(t, 0) + 1
                        for c, t in zip(curr, target):
                            if c == t:
                                target_counts[c] -= 1

                        correct_char = 0
                        for c, t in zip(curr, target):
                            if c != t and target_counts.get(c, 0) > 0:
                                correct_char += 1
                                target_counts[c] -= 1

                        state["guesses"].append(
                            {"guess": curr, "correct_pos": correct_pos, "correct_char": correct_char}
                        )
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

@router.post("/chat")
async def chat(action: PlayerAction):
    loop = asyncio.get_running_loop()

    def event_stream():
        with get_session() as session:
            for item in engine.process_action(action, session):
                if isinstance(item, str):
                    yield f"data: {json.dumps({'chunk': item})}\n\n"
                elif isinstance(item, dict):
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast(
                            json.dumps({"type": "narrative_event", "data": item, "action": action.model_dump()})
                        ),
                        loop,
                    )

                    if item.get("state_updates", {}).get("minigame_trigger"):
                        asyncio.run_coroutine_threadsafe(
                            manager.broadcast(
                                json.dumps(
                                    {
                                        "type": "trigger_minigame",
                                        "minigame_type": item["state_updates"]["minigame_trigger"],
                                        "character_id": action.character_id,
                                    }
                                )
                            ),
                            loop,
                        )

                    for event in item.get("events", []):
                        if isinstance(event, dict) and event.get("type") == "npc_state_change":
                            asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps(event)), loop)

                    yield f"data: {json.dumps({'result': item})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/quests")
async def get_quests(character_id: int):
    with get_session() as session:
        quests = session.exec(select(QuestState).where(QuestState.character_id == character_id)).all()
        return quests

@router.get("/history")
async def get_history(limit: int = 50):
    from backend.database import LedgerEntry
    with get_session() as session:
        entries = session.exec(select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(limit)).all()
        return entries

@router.post("/generate_npc")
async def generate_npc_endpoint(flavor: str = "industrial"):
    from backend.npc_generator import generate_procedural_npc
    with get_session() as session:
        npc = generate_procedural_npc(session, location_flavor=flavor)
        return npc

@router.post("/characters/generate-gear")
async def generate_gear(req: GenerateGearRequest):
    if not req.gear_prompt:
        return {"items": []}

    client = VLLMClient()
    prompt = (
        f"You are the game master. The player chose class '{req.preset}' and requested starting gear: '{req.gear_prompt}'. "
        "Grant them 1-3 reasonable starting items. Do not give them overpowered items; powerful items must be acquired in-game. "
        "The category must be one of: Consumables, Equipment, Crafting_Materials, Steam_Tech_Components. "
        'Return ONLY a JSON array of items: [{"name": "Rusty Wrench", "description": "A heavy wrench.", "quantity": 1, "category": "Equipment"}]'
    )
    try:
        response = client.generate(prompt=prompt, max_tokens=200, temperature=0.7)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
            items = json.loads(json_match.group(0))
            return {"items": items}
        return {"items": []}
    except Exception as e:
        print(f"Failed to generate gear: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate gear")

@router.post("/characters/{character_id}/settings/tutorials")
async def toggle_tutorials(character_id: int, req: ToggleTutorialsRequest):
    with get_session() as session:
        char = session.exec(select(Character).where(Character.id == character_id)).first()
        if not char:
            raise HTTPException(status_code=404, detail="Character not found")
        char.show_tutorials = req.show_tutorials
        session.add(char)
        session.commit()
        session.refresh(char)
        return {"status": "success", "show_tutorials": char.show_tutorials}

@router.get("/characters/{character_id}")
async def get_character(character_id: int):
    with get_session() as session:
        char = session.exec(select(Character).where(Character.id == character_id)).first()
        if not char:
            raise HTTPException(status_code=404, detail="Character not found")
        return char

@router.post("/characters")
async def create_character(req: CharacterCreateRequest):
    preset_data = PRESETS.get(req.preset, PRESETS["Wanderer"])
    with get_session() as session:
        char = Character(
            name=req.name,
            character_class=req.preset,
            background=req.backstory if req.backstory.strip() else preset_data["background"],
            stats=preset_data["stats"],
            show_tutorials=req.show_tutorials,
            user_id=req.user_id,
        )
        session.add(char)
        session.commit()
        session.refresh(char)

        if req.gear and len(req.gear) > 0:
            for item_data in req.gear:
                cat_str = item_data.get("category", "Equipment")
                try:
                    category = ItemCategory(cat_str)
                except ValueError:
                    category = ItemCategory.equipment

                item = DBItem(
                    name=item_data.get("name", "Unknown Item"),
                    description=item_data.get("description", ""),
                    category=category,
                )
                session.add(item)
                session.commit()
                session.refresh(item)

                inv = Inventory(character_id=char.id, item_id=item.id, quantity=item_data.get("quantity", 1))
                session.add(inv)
            session.commit()
            session.refresh(char)

        client = VLLMClient()
        quest_prompt = (
            f"You are the game master. The player character '{char.name}' has the following background: '{char.background}'. "
            "Generate a singular, grand, long-term overarching quest/goal for them in the steampunk world of Shangri-la. "
            'Return ONLY a JSON object: {"title": "Quest Title", "description": "A long detailed description of the overarching goal."}'
        )
        try:
            response = client.generate(prompt=quest_prompt, max_tokens=150, temperature=0.7)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                quest_data = json.loads(json_match.group(0))
                quest = Quest(
                    title=quest_data.get("title", "A Grand Endeavor"),
                    description=quest_data.get("description", "A long journey awaits."),
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

@router.post("/minigames/start")
async def start_minigame(character_id: int, game_type: str = "gear_lock"):
    with get_session() as session:
        state = {}
        if game_type == "gear_lock":
            state = {"gears": [0, 0, 0], "target": [5, 5, 5]}
        game = Minigame(character_id=character_id, type=game_type, state=state, solved=False)
        session.add(game)
        session.commit()
        session.refresh(game)
        return game

@router.post("/minigames/{minigame_id}/action")
async def perform_minigame_action(minigame_id: int, req: MinigameActionRequest):
    with get_session() as session:
        game = session.exec(select(Minigame).where(Minigame.id == minigame_id)).first()
        if not game:
            raise HTTPException(status_code=404, detail="Minigame not found")

        if req.action == "solve_cheat":
            game.solved = True
        elif game.type == "gear_lock":
            game.state["gears"] = game.state["target"]
            game.solved = True

        session.add(game)
        session.commit()
        session.refresh(game)
        return game

@router.post("/airships/acquire")
async def acquire_airship(character_id: int, name: str):
    with get_session() as session:
        ship = Airship(character_id=character_id, name=name)
        session.add(ship)
        session.commit()
        session.refresh(ship)
        return ship

@router.post("/airships/{airship_id}/install_module")
async def install_airship_module(airship_id: int, module_name: str):
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

@router.post("/airships/{airship_id}/fly")
async def fly_airship(airship_id: int, altitude: int, distance: float):
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
