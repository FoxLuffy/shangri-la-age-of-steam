from typing import List, Optional, Dict, Any
from sqlmodel import Session as SQLModelSession, select
from backend.database import engine, Location as DBLocation, NPC as DBNPC, WorldState as DBWorldState
from backend.models import WorldState, Location, NPC
from backend.database_init import seed_data

class StateRepository:
    def __init__(self, session: SQLModelSession):
        self.session = session

    def get_latest_state(self) -> WorldState:
        db_state = self.session.exec(select(DBWorldState).order_by(DBWorldState.id.desc())).first()
        if not db_state:
            seed_data()
            db_state = self.session.exec(select(DBWorldState).order_by(DBWorldState.id.desc())).first()

        loc_id = db_state.current_location_id if db_state else "1"
        db_loc = self.session.get(DBLocation, loc_id)
        if not db_loc:
            current_location = Location(
                id=loc_id,
                name="The Rusty Anchor Tavern",
                description="A dim, steam-filled tavern near the docks.",
                npcs=[]
            )
        else:
            current_location = Location(
                id=db_loc.id,
                name=db_loc.name,
                description=db_loc.description,
                npcs=[npc.id for npc in db_loc.npcs] if hasattr(db_loc, "npcs") and db_loc.npcs and isinstance(db_loc.npcs[0], DBNPC) else (db_loc.npcs or [])
            )

        active_npc_ids = db_state.active_npcs_ids if db_state and db_state.active_npcs_ids else []
        active_npcs: List[NPC] = []
        for npc_id in active_npc_ids:
            db_npc = self.session.get(DBNPC, npc_id)
            if db_npc:
                active_npcs.append(NPC(
                    id=db_npc.id,
                    name=db_npc.name,
                    traits=db_npc.traits or [],
                    current_dialogue=db_npc.current_dialogue,
                    disposition=db_npc.disposition if db_npc.disposition is not None else 0.0,
                    memories=db_npc.memories or [],
                    faction_id=db_npc.faction_id,
                    hp=db_npc.hp,
                    max_hp=db_npc.max_hp,
                    armor=db_npc.armor,
                    status_effects=db_npc.status_effects or [],
                    is_hostile=db_npc.is_hostile
                ))

        from backend.database import Inventory, Item, Quest, QuestState, Character

        inventory_list = []
        quests_list = []
        
        # We assume single-player character_id = 1 for now
        char = self.session.get(Character, 1)
        if char:
            inv_items = self.session.exec(select(Inventory).where(Inventory.character_id == char.id)).all()
            for inv in inv_items:
                item = self.session.get(Item, inv.item_id)
                if item:
                    inventory_list.append({
                        "name": item.name,
                        "description": item.description,
                        "quantity": inv.quantity
                    })
            
            q_states = self.session.exec(select(QuestState).where(QuestState.character_id == char.id)).all()
            for qs in q_states:
                quest = self.session.get(Quest, qs.quest_id)
                if quest:
                    quests_list.append({
                        "title": quest.title,
                        "description": quest.description,
                        "state": qs.state
                    })
                    
            from backend.database import Minigame, Faction, FactionStanding
            
            factions_list = []
            f_states = self.session.exec(select(FactionStanding).where(FactionStanding.character_id == char.id)).all()
            for fs in f_states:
                faction = self.session.get(Faction, fs.faction_id)
                if faction:
                    factions_list.append({
                        "faction_id": faction.id,
                        "faction_name": faction.name,
                        "standing": fs.standing
                    })
                    
            mg = self.session.exec(select(Minigame).where(Minigame.character_id == char.id, Minigame.solved == False)).first()
            if mg:
                active_minigame = {
                    "id": mg.id,
                    "type": mg.type,
                    "state": mg.state
                }
            else:
                active_minigame = None
        else:
            active_minigame = None

        return WorldState(
            current_location_id=current_location.id,
            active_npcs_ids=active_npc_ids,
            global_event=db_state.global_event if db_state else None,
            world_memories=db_state.world_memories if db_state else [],
            current_location=current_location,
            active_npcs=active_npcs,
            inventory=inventory_list,
            quests=quests_list,
            factions=factions_list if 'factions_list' in locals() else [],
            active_minigame=active_minigame,
            is_combat_active=db_state.is_combat_active if db_state else False,
            player_stats={
                "hp": char.hp,
                "max_hp": char.max_hp,
                "armor": char.armor,
                "steam": char.steam,
                "max_steam": char.max_steam,
                "status_effects": char.status_effects or []
            } if char else None
        )

    def save_state(self, state: WorldState) -> WorldState:
        db_state = DBWorldState(
            current_location_id=state.current_location_id,
            active_npcs_ids=state.active_npcs_ids if isinstance(state.active_npcs_ids, list) else [],
            global_event=state.global_event,
            world_memories=state.world_memories if isinstance(state.world_memories, list) else []
        )
        self.session.add(db_state)
        self.session.commit()
        self.session.refresh(db_state)
        return state

    def update_location(self, location_id: str, data: Dict[str, Any]) -> Optional[DBLocation]:
        location = self.session.get(DBLocation, location_id)
        if location:
            for key, value in data.items():
                if hasattr(location, key) and key != "id":
                    setattr(location, key, value)
            self.session.add(location)
            self.session.commit()
            self.session.refresh(location)
        return location

    def update_npc(self, npc_id: str, disposition_delta: Optional[float] = None, new_memory: Optional[Dict[str, str]] = None) -> Optional[DBNPC]:
        npc = self.session.get(DBNPC, npc_id)
        if npc:
            if disposition_delta is not None:
                npc.disposition = max(-1.0, min(1.0, npc.disposition + disposition_delta))
            if new_memory:
                memories = list(npc.memories or [])
                memories.append(new_memory)
                npc.memories = memories
            self.session.commit()
            self.session.refresh(npc)
        return npc

    def create_or_update_npc(self, npc_data: Dict[str, Any], location_id: str) -> DBNPC:
        npc_id = npc_data.get("id") or npc_data.get("name", "npc_unknown").lower().replace(" ", "_")
        npc = self.session.get(DBNPC, npc_id)
        if not npc:
            npc = DBNPC(
                id=npc_id,
                name=npc_data.get("name", "Unknown NPC"),
                traits=npc_data.get("traits", []),
                disposition=npc_data.get("disposition", 0.0),
                location_id=location_id
            )
        else:
            if "name" in npc_data:
                npc.name = npc_data["name"]
            if "traits" in npc_data:
                npc.traits = npc_data["traits"]
            if "disposition" in npc_data:
                npc.disposition = npc_data["disposition"]
        self.session.add(npc)
        self.session.commit()
        self.session.refresh(npc)
        return npc

    def record_ledger_entry(self, action: str, narration: str, state_updates: Dict[str, Any], events: List[Dict[str, Any]], location_id: Optional[str] = None):
        from backend.database import LedgerEntry
        from datetime import datetime
        entry = LedgerEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            action=action,
            narration=narration,
            state_updates=state_updates,
            events=events,
            location_id=location_id
        )
        self.session.add(entry)
        self.session.commit()
        return entry

    def apply_inventory_update(self, update: Dict[str, Any]):
        from backend.database import Inventory, Item, Character
        
        char_id = 1
        action = update.get("action", "add")
        item_name = update.get("item_name")
        qty = update.get("quantity", 1)
        if not item_name:
            return
            
        # Find or create item
        item = self.session.exec(select(Item).where(Item.name == item_name)).first()
        if not item:
            item = Item(name=item_name, description=update.get("description", "A mysterious item."), category="Consumables")
            self.session.add(item)
            self.session.commit()
            self.session.refresh(item)
            
        inv = self.session.exec(select(Inventory).where(Inventory.character_id == char_id, Inventory.item_id == item.id)).first()
        
        if action == "add":
            if inv:
                inv.quantity += qty
            else:
                inv = Inventory(character_id=char_id, item_id=item.id, quantity=qty)
            self.session.add(inv)
        elif action == "remove":
            if inv:
                inv.quantity -= qty
                if inv.quantity <= 0:
                    self.session.delete(inv)
                else:
                    self.session.add(inv)
                    
        self.session.commit()

    def apply_quest_update(self, update: Dict[str, Any]):
        from backend.database import Quest, QuestState, QuestStateEnum
        
        char_id = 1
        action = update.get("action", "add")
        title = update.get("quest_title")
        if not title:
            return
            
        quest = self.session.exec(select(Quest).where(Quest.title == title)).first()
        if not quest:
            quest = Quest(title=title, description=update.get("description", ""))
            self.session.add(quest)
            self.session.commit()
            self.session.refresh(quest)
        elif update.get("description"):
            # Update description if provided
            quest.description = update["description"]
            self.session.add(quest)
            self.session.commit()
            
        q_state = self.session.exec(select(QuestState).where(QuestState.character_id == char_id, QuestState.quest_id == quest.id)).first()
        
        state_val = QuestStateEnum.active
        if action == "complete":
            state_val = QuestStateEnum.completed
        elif action == "fail":
            state_val = QuestStateEnum.failed
            
        if not q_state:
            q_state = QuestState(character_id=char_id, quest_id=quest.id, state=state_val)
        else:
            q_state.state = state_val
            
        self.session.add(q_state)
        self.session.commit()

    def trigger_minigame(self, minigame_type: str):
        from backend.database import Minigame, Character
        char_id = 1
        
        # Check if already exists
        existing = self.session.exec(select(Minigame).where(Minigame.character_id == char_id, Minigame.solved == False)).first()
        if existing:
            return
            
        state = {}
        if minigame_type == "hack":
            state = {
                "sequence": ["A", "B", "C"], # Dummy sequence
                "current_input": [],
                "attempts_left": 3,
                "message": "Terminal locked. Enter bypass sequence."
            }
        elif minigame_type == "lockpick":
            state = {
                "pins": [False, False, False],
                "message": "3 pins to set. Careful not to break the pick."
            }
            
        minigame = Minigame(character_id=char_id, type=minigame_type, state=state, solved=False)
        self.session.add(minigame)
        self.session.commit()

    def apply_faction_update(self, update: Dict[str, Any]):
        from backend.database import FactionStanding
        char_id = 1
        faction_id = update.get("faction_id")
        change = update.get("change", 0.0)
        
        if not faction_id:
            return
            
        fs = self.session.exec(select(FactionStanding).where(FactionStanding.character_id == char_id, FactionStanding.faction_id == faction_id)).first()
        if not fs:
            fs = FactionStanding(character_id=char_id, faction_id=faction_id, standing=0.0)
            
        fs.standing += float(change)
        
        # Clamp between -1.0 and 1.0
        fs.standing = max(-1.0, min(1.0, fs.standing))
        
        self.session.add(fs)
        self.session.commit()

    def apply_combat_update(self, update: Dict[str, Any]):
        from backend.database import Character, NPC, WorldState as DBWorldState
        char_id = 1
        
        # Update WorldState is_combat_active
        db_state = self.session.exec(select(DBWorldState)).first()
        if db_state and "is_combat_active" in update:
            db_state.is_combat_active = update["is_combat_active"]
            self.session.add(db_state)
            
        # Update Player
        player_updates = update.get("player_updates", {})
        if player_updates:
            char = self.session.get(Character, char_id)
            if char:
                char.hp += player_updates.get("hp_change", 0)
                char.steam += player_updates.get("steam_change", 0)
                char.hp = max(0, min(char.max_hp, char.hp))
                char.steam = max(0, min(char.max_steam, char.steam))
                
                # Handling status effects
                current_effects = set(char.status_effects or [])
                for eff in player_updates.get("status_effects_add", []):
                    current_effects.add(eff)
                for eff in player_updates.get("status_effects_remove", []):
                    current_effects.discard(eff)
                char.status_effects = list(current_effects)
                self.session.add(char)
                
        # Update NPCs
        npc_updates = update.get("npc_updates", [])
        for npc_u in npc_updates:
            npc_id = npc_u.get("npc_id")
            if not npc_id:
                continue
            npc = self.session.get(NPC, npc_id)
            if npc:
                npc.hp += npc_u.get("hp_change", 0)
                npc.hp = max(0, min(npc.max_hp, npc.hp))
                
                current_effects = set(npc.status_effects or [])
                for eff in npc_u.get("status_effects_add", []):
                    current_effects.add(eff)
                for eff in npc_u.get("status_effects_remove", []):
                    current_effects.discard(eff)
                npc.status_effects = list(current_effects)
                self.session.add(npc)
                
        self.session.commit()

if __name__ == "__main__":
    with get_session() as session:
        repo = StateRepository(session)
        pass
