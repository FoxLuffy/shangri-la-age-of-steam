import asyncio
import json
import os
import random
import re
from typing import Optional

from backend.client import VLLMClient
from backend.database import NPC as DBNPC
from backend.database import (
    Airship,
    Artifact,
    BulletinBoardMessage,
    Character,
    Guild,
    Inventory,
    ItemCategory,
    Minigame,
    Quest,
    QuestState,
    QuestStateEnum,
    TradeHistory,
    get_session,
)
from backend.database import Item as DBItem
from backend.database import Location as DBLocation
from backend.engine import NarrativeEngine
from backend.models import PlayerAction
from backend.repository import StateRepository
from backend.schemas import (
    AirshipNavigateRequest,
    AugmentationInstallRequest,
    BountyAcceptRequest,
    BulletinMessageRequest,
    CharacterCreateRequest,
    GenerateGearRequest,
    GuildCreateRequest,
    GuildInviteRequest,
    MinigameActionRequest,
    MinigamePlayPayload,
    ToggleTutorialsRequest,
    TradeAcceptRequest,
    TradeOfferRequest,
)
from backend.timeutils import utcnow_naive
from backend.websocket import manager
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

AUGMENTATION_CATALOG = [
    {
        "id": "pneumatic_arm",
        "name": "Pneumatic Arm",
        "body_part": "arm",
        "cost": 200,
        "strain": 10,
        "stats": {"strength": 2, "hp": 10}
    },
    {
        "id": "clockwork_legs",
        "name": "Clockwork Legs",
        "body_part": "legs",
        "cost": 250,
        "strain": 12,
        "stats": {"speed": 2}
    },
    {
        "id": "optic_sensor",
        "name": "Optic Sensor",
        "body_part": "eye",
        "cost": 150,
        "strain": 5,
        "stats": {"intellect": 1}
    }
]

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

ORIGINS = {
    "Foundry Orphan": {
        "items": [
            {"name": "Soot-Stained Rag", "description": "A dirty rag from the foundry.", "quantity": 1, "category": "Equipment"},
            {"name": "Scrap Metal", "description": "A piece of scrap metal.", "quantity": 3, "category": "Crafting_Materials"}
        ],
        "npc_disposition": {"npc_name": "Foreman Ironfist", "bump": 0.3}
    },
    "Aristocratic Heir": {
        "items": [
            {"name": "Signet Ring", "description": "A family signet ring.", "quantity": 1, "category": "Equipment"},
            {"name": "Fine Wine", "description": "A bottle of expensive wine.", "quantity": 1, "category": "Consumables"}
        ],
        "npc_disposition": {"npc_name": "Lord Sterling", "bump": 0.3}
    },
    "Guild Apprentice": {
        "items": [
            {"name": "Apprentice Badge", "description": "A badge of the guild.", "quantity": 1, "category": "Equipment"},
            {"name": "Basic Tools", "description": "Basic crafting tools.", "quantity": 1, "category": "Equipment"}
        ],
        "npc_disposition": {"npc_name": "Master Craftsman", "bump": 0.3}
    },
    "Smuggler's Ward": {
        "items": [
            {"name": "Lockpick Set", "description": "A set of lockpicks.", "quantity": 1, "category": "Equipment"},
            {"name": "Smuggler's Map", "description": "A map of secret routes.", "quantity": 1, "category": "Equipment"}
        ],
        "npc_disposition": {"npc_name": "Sly The Fox", "bump": 0.3}
    },
    "Automata Tinkerer": {
        "items": [
            {"name": "Spare Gear", "description": "A spare brass gear.", "quantity": 5, "category": "Steam_Tech_Components"},
            {"name": "Wrench", "description": "A trusty wrench.", "quantity": 1, "category": "Equipment"}
        ],
        "npc_disposition": {"npc_name": "Tinkerer Tom", "bump": 0.3}
    }
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

@router.get("/bounties")
async def get_bounties(character_id: int):
    from backend.database import Bounty
    with get_session() as session:
        # Get character to retrieve their active and completed bounties
        char = session.get(Character, character_id)
        if not char:
            raise HTTPException(status_code=404, detail="Character not found")

        # Get available bounties (we can procedurally generate if none exist)
        available = session.exec(select(Bounty).where(Bounty.status == "available")).all()

        if len(available) < 3:
            import random
            targets = ["Automata", "Thug", "Smuggler", "Cultist", "Pirate"]
            adjectives = ["Rogue", "Notorious", "Dangerous", "Wanted", "Crazed"]
            for _ in range(3 - len(available)):
                target = random.choice(targets)
                adj = random.choice(adjectives)
                bounty = Bounty(
                    title=f"Bounty: {adj} {target}",
                    description=f"A {adj.lower()} {target.lower()} has been causing trouble. Eliminate them for a reward.",
                    target_npc_type=target,
                    reward_coins=random.randint(50, 150),
                    status="available"
                )
                session.add(bounty)
            session.commit()
            available = session.exec(select(Bounty).where(Bounty.status == "available")).all()

        active = [b for b in (session.get(Bounty, bid) for bid in (char.active_bounties or [])) if b]

        return {
            "available": available,
            "active": active,
            "active_ids": char.active_bounties or [],
            "completed_ids": char.completed_bounties or []
        }

@router.post("/bounties/accept")
async def accept_bounty(character_id: int, req: BountyAcceptRequest):
    from backend.database import Bounty
    with get_session() as session:
        char = session.get(Character, character_id)
        if not char:
            raise HTTPException(status_code=404, detail="Character not found")

        bounty = session.get(Bounty, req.bounty_id)
        if not bounty:
            raise HTTPException(status_code=404, detail="Bounty not found")

        if bounty.status != "available":
            raise HTTPException(status_code=400, detail="Bounty is not available")

        # One active bounty at a time: accepting a new one abandons any current active
        # bounty (returned to the pool) and replaces it.
        for old_id in list(char.active_bounties or []):
            if old_id == bounty.id:
                continue
            old = session.get(Bounty, old_id)
            if old and old.status == "active":
                old.status = "available"
                session.add(old)

        bounty.status = "active"
        char.active_bounties = [bounty.id]

        session.add(bounty)
        session.add(char)
        session.commit()
        return {"status": "success", "bounty": bounty}

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
async def get_character(character_id: int, session: Session = Depends(get_session)):
    char = session.exec(select(Character).where(Character.id == character_id)).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    # Apply artifact bonuses dynamically
    if char.discovered_artifacts:
        artifacts = session.exec(select(Artifact).where(Artifact.id.in_(char.discovered_artifacts))).all()
        bonus_stats = dict(char.stats)
        for art in artifacts:
            for stat, bonus in art.stat_bonus.items():
                bonus_stats[stat] = bonus_stats.get(stat, 0) + bonus
        char.stats = bonus_stats

    return char

@router.get("/artifacts")
async def get_artifacts(session: Session = Depends(get_session)):
    artifacts = session.exec(select(Artifact)).all()
    return artifacts


@router.get("/journal")
async def get_journal(character_id: int, session: Session = Depends(get_session)):
    """Explorer's Journal (C2): the character's discovery log — places visited, people met,
    and the artifact codex (discovered vs undiscovered)."""
    from backend.database import Location as DBLocation

    char = session.get(Character, character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    places = []
    for loc_id in char.visited_locations or []:
        loc = session.get(DBLocation, loc_id)
        if loc:
            places.append({"id": loc.id, "name": loc.name, "description": loc.description})

    people = []
    for nid in char.met_npcs or []:
        npc = session.get(DBNPC, nid)
        if npc:
            people.append({"id": npc.id, "name": npc.name, "traits": npc.traits or []})

    discovered = set(char.discovered_artifacts or [])
    artifacts = [
        {
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "rarity": a.rarity,
            "stat_bonus": a.stat_bonus,
            "discovered": a.id in discovered,
        }
        for a in session.exec(select(Artifact)).all()
    ]

    return {"places": places, "people": people, "artifacts": artifacts}

@router.post("/artifacts/discover")
async def discover_artifact(character_id: int, artifact_id: int, session: Session = Depends(get_session)):
    char = session.get(Character, character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    artifact = session.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    artifacts = list(char.discovered_artifacts or [])
    if artifact_id not in artifacts:
        artifacts.append(artifact_id)
        char.discovered_artifacts = artifacts
        session.add(char)
        session.commit()

    return {"status": "success", "artifact": artifact, "character_id": character_id}

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

        if req.origin and req.origin in ORIGINS:
            origin_data = ORIGINS[req.origin]
            for item_data in origin_data["items"]:
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

            npc_info = origin_data["npc_disposition"]
            npc = session.exec(select(DBNPC).where(DBNPC.name == npc_info["npc_name"])).first()
            if not npc:
                npc = DBNPC(id=npc_info["npc_name"].lower().replace(" ", "_"), name=npc_info["npc_name"], disposition=npc_info["bump"], location_id="1")
            else:
                npc.disposition += npc_info["bump"]
            session.add(npc)
            session.commit()

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

@router.post("/airships/navigate")
async def navigate_airship(req: AirshipNavigateRequest):
    with get_session() as session:
        char = session.exec(select(Character).where(Character.id == req.character_id)).first()
        if not char:
            raise HTTPException(status_code=404, detail="Character not found")

        ship = session.exec(select(Airship).where(Airship.character_id == req.character_id)).first()
        if not ship:
            raise HTTPException(status_code=404, detail="Airship not found")

        fuel_cost = 15.0 # Fixed rate or based on distance
        if ship.fuel_level < fuel_cost:
            raise HTTPException(status_code=400, detail="Not enough fuel")

        ship.fuel_level -= fuel_cost

        encounter_trigger = random.random() < 0.3
        narration = f"You fired up the {ship.name}'s steam engines and successfully navigated to location {req.location_id}."
        if encounter_trigger:
            damage = 10.0
            ship.hull_integrity -= damage
            narration = f"During your flight to location {req.location_id}, the {ship.name} encountered heavy aether storms! You lost {damage} hull integrity, but managed to land."

        char.location_id = req.location_id

        session.add(ship)
        session.add(char)
        session.commit()
        session.refresh(ship)
        session.refresh(char)

        return {
            "ship": ship,
            "character": char,
            "narration": narration
        }

@router.get("/airships")
async def get_airship(character_id: int):
    with get_session() as session:
        ship = session.exec(select(Airship).where(Airship.character_id == character_id)).first()
        if not ship:
            raise HTTPException(status_code=404, detail="Airship not found")
        return ship

@router.get("/codex")
async def get_codex():
    import json
    import os

    codex_path = os.path.join(os.path.dirname(__file__), "..", "codex")
    codex_data = {}

    if os.path.exists(codex_path):
        for category in os.listdir(codex_path):
            category_path = os.path.join(codex_path, category)
            if os.path.isdir(category_path):
                codex_data[category] = []
                for filename in os.listdir(category_path):
                    if filename.endswith(".json"):
                        file_path = os.path.join(category_path, filename)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                codex_data[category].append(json.load(f))
                        except Exception as e:
                            print(f"Error loading codex file {file_path}: {e}")
    return codex_data

@router.get("/augmentations/catalog")
async def get_augmentation_catalog():
    return AUGMENTATION_CATALOG

@router.post("/augmentations/install")
async def install_augmentation(req: AugmentationInstallRequest):
    from backend.database import Augmentation
    aug_data = next((a for a in AUGMENTATION_CATALOG if a["id"] == req.augmentation_id), None)
    if not aug_data:
        raise HTTPException(status_code=404, detail="Augmentation not found")

    with get_session() as session:
        char = session.exec(select(Character).where(Character.id == req.character_id)).first()
        if not char:
            raise HTTPException(status_code=404, detail="Character not found")

        if char.brass_coins < aug_data["cost"]:
            raise HTTPException(status_code=400, detail="Not enough brass coins")

        char.brass_coins -= aug_data["cost"]
        char.total_strain = getattr(char, "total_strain", 0) + aug_data["strain"]

        aug = Augmentation(
            character_id=char.id,
            body_part=aug_data["body_part"],
            augmentation_name=aug_data["name"],
            stat_bonus=aug_data["stats"]
        )
        session.add(aug)
        session.add(char)
        session.commit()
        session.refresh(char)

        return {
            "status": "success",
            "augmentation": {
                "id": aug.id,
                "body_part": aug.body_part,
                "augmentation_name": aug.augmentation_name,
                "stat_bonus": aug.stat_bonus
            },
            "character_strain": char.total_strain,
            "brass_coins": char.brass_coins
        }

@router.post("/trade/offer")
async def trade_offer(initiator_id: int, req: TradeOfferRequest):
    with get_session() as session:
        trade = TradeHistory(
            initiator_id=initiator_id,
            receiver_id=req.receiver_id,
            initiator_item_id=req.initiator_item_id,
            initiator_coins=req.initiator_coins,
            receiver_item_id=req.receiver_item_id,
            receiver_coins=req.receiver_coins,
            status="pending",
            timestamp=utcnow_naive().isoformat()
        )
        session.add(trade)
        session.commit()
        session.refresh(trade)
        return trade

@router.post("/trade/accept")
async def trade_accept(character_id: int, req: TradeAcceptRequest):
    with get_session() as session:
        trade = session.exec(select(TradeHistory).where(TradeHistory.id == req.trade_id)).first()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        if trade.receiver_id != character_id:
            raise HTTPException(status_code=403, detail="Not the receiver of this trade")
        if trade.status != "pending":
            raise HTTPException(status_code=400, detail="Trade is not pending")

        if not req.accept:
            trade.status = "rejected"
            session.add(trade)
            session.commit()
            return {"status": "rejected"}

        # For simplicity, we assume they have the items and coins, and we just swap them.
        initiator = session.get(Character, trade.initiator_id)
        receiver = session.get(Character, trade.receiver_id)

        if initiator.brass_coins < trade.initiator_coins or receiver.brass_coins < trade.receiver_coins:
            raise HTTPException(status_code=400, detail="Insufficient coins")

        initiator.brass_coins += trade.receiver_coins - trade.initiator_coins
        receiver.brass_coins += trade.initiator_coins - trade.receiver_coins

        # Move items if present
        if trade.initiator_item_id:
            i_inv = session.exec(select(Inventory).where(Inventory.character_id == initiator.id, Inventory.item_id == trade.initiator_item_id)).first()
            if i_inv and i_inv.quantity > 0:
                i_inv.quantity -= 1
                r_inv = session.exec(select(Inventory).where(Inventory.character_id == receiver.id, Inventory.item_id == trade.initiator_item_id)).first()
                if r_inv:
                    r_inv.quantity += 1
                else:
                    session.add(Inventory(character_id=receiver.id, item_id=trade.initiator_item_id, quantity=1))
                session.add(i_inv)

        if trade.receiver_item_id:
            r_inv = session.exec(select(Inventory).where(Inventory.character_id == receiver.id, Inventory.item_id == trade.receiver_item_id)).first()
            if r_inv and r_inv.quantity > 0:
                r_inv.quantity -= 1
                i_inv = session.exec(select(Inventory).where(Inventory.character_id == initiator.id, Inventory.item_id == trade.receiver_item_id)).first()
                if i_inv:
                    i_inv.quantity += 1
                else:
                    session.add(Inventory(character_id=initiator.id, item_id=trade.receiver_item_id, quantity=1))
                session.add(r_inv)

        trade.status = "accepted"
        session.add(trade)
        session.add(initiator)
        session.add(receiver)
        session.commit()
        return {"status": "accepted"}

@router.post("/guilds/create")
async def create_guild(character_id: int, req: GuildCreateRequest):
    with get_session() as session:
        char = session.get(Character, character_id)
        if not char:
            raise HTTPException(status_code=404, detail="Character not found")
        if char.guild_id:
            raise HTTPException(status_code=400, detail="Character already in a guild")

        guild = Guild(name=req.name, description=req.description, leader_id=character_id)
        session.add(guild)
        session.commit()
        session.refresh(guild)

        char.guild_id = guild.id
        session.add(char)
        session.commit()
        return {"id": guild.id, "name": guild.name, "description": guild.description, "treasury": guild.treasury, "leader_id": guild.leader_id}

@router.post("/guilds/invite")
async def invite_guild(leader_id: int, req: GuildInviteRequest):
    with get_session() as session:
        guild = session.get(Guild, req.guild_id)
        if not guild or guild.leader_id != leader_id:
            raise HTTPException(status_code=403, detail="Not guild leader")

        target = session.get(Character, req.character_id)
        if not target:
            raise HTTPException(status_code=404, detail="Target character not found")

        target.guild_id = guild.id
        session.add(target)
        session.commit()
        return {"status": "success", "message": f"{target.name} added to guild"}

@router.get("/guilds/treasury")
async def get_guild_treasury(guild_id: int):
    with get_session() as session:
        guild = session.get(Guild, guild_id)
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")

        members = session.exec(select(Character).where(Character.guild_id == guild.id)).all()
        return {
            "guild": guild,
            "members": [m.name for m in members],
            "treasury": guild.treasury
        }

@router.post("/messages/send")
async def send_message(character_id: int, req: BulletinMessageRequest):
    with get_session() as session:
        msg = BulletinBoardMessage(
            location_id=req.location_id,
            author_id=character_id,
            content=req.content,
            timestamp=utcnow_naive().isoformat()
        )
        session.add(msg)
        session.commit()
        session.refresh(msg)
        return msg

@router.get("/messages/board")
async def get_messages(location_id: str):
    with get_session() as session:
        msgs = session.exec(select(BulletinBoardMessage).where(BulletinBoardMessage.location_id == location_id).order_by(BulletinBoardMessage.id.desc()).limit(50)).all()
        return msgs



