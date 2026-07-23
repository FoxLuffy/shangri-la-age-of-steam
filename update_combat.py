import json
import re

# 1. Update backend/repository.py apply_combat_update
with open('backend/repository.py', 'r') as f:
    repo_content = f.read()

repo_content = re.sub(
    r'def apply_combat_update\(self, update: Dict\[str, Any\], char_id: int\):.*?self\.session\.commit\(\)',
    '''def apply_combat_update(self, update: Dict[str, Any], char_id: int):
        from backend.database import Character, NPC, WorldState as DBWorldState, CombatSession

        # Get character to find location
        char = self.session.get(Character, char_id)
        if not char: return
        loc_id = char.location_id

        # Update WorldState is_combat_active
        db_state = self.session.exec(select(DBWorldState).order_by(DBWorldState.id.desc())).first()
        if db_state and "is_combat_active" in update:
            db_state.is_combat_active = update["is_combat_active"]
            self.session.add(db_state)
            
            # Manage CombatSession
            combat_session = self.session.exec(select(CombatSession).where(CombatSession.location_id == loc_id)).first()
            if update["is_combat_active"]:
                if not combat_session or not combat_session.is_active:
                    # Start combat session
                    active_npc_ids = db_state.active_npcs_ids if isinstance(db_state.active_npcs_ids, list) else []
                    
                    participants = []
                    # Get all players in this location
                    players = self.session.exec(select(Character).where(Character.location_id == loc_id)).all()
                    for p in players:
                        participants.append({
                            "id": f"player_{p.id}",
                            "type": "player",
                            "name": p.name,
                            "speed": p.stats.get("speed", 5) if p.stats else 5
                        })
                        
                    for npc_id in active_npc_ids:
                        n = self.session.get(NPC, npc_id)
                        if n:
                            participants.append({
                                "id": f"npc_{n.id}",
                                "type": "npc",
                                "name": n.name,
                                "speed": getattr(n, "speed", 5)
                            })
                            
                    # Sort by speed descending
                    participants.sort(key=lambda x: x["speed"], reverse=True)
                    
                    if not combat_session:
                        combat_session = CombatSession(location_id=loc_id, is_active=True, turn_order=participants, current_turn_index=0)
                    else:
                        combat_session.is_active = True
                        combat_session.turn_order = participants
                        combat_session.current_turn_index = 0
                    self.session.add(combat_session)
                else:
                    # Advance turn if needed or if explicitly advanced
                    pass
            else:
                if combat_session:
                    combat_session.is_active = False
                    self.session.add(combat_session)

        # Update Player
        player_updates = update.get("player_updates", {})
        if player_updates:
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
                
        self.session.commit()''',
    repo_content,
    flags=re.DOTALL
)

with open('backend/repository.py', 'w') as f:
    f.write(repo_content)

print("Updated backend/repository.py")
