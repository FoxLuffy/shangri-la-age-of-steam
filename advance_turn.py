import re

with open('backend/engine.py', 'r') as f:
    content = f.read()

# At the end of process_action, advance turn if it was this player's turn.
# Search for yield { ... "is_combat_active": getattr(state, "is_combat_active", False) }
# It's at the end of the method.
replacement = '''        
        if repository and getattr(state, "is_combat_active", False) and getattr(state, "combat_state", None):
            cs = state.combat_state
            turn_order = cs.get("turn_order", [])
            idx = cs.get("current_turn_index", 0)
            if turn_order:
                # Advance turn
                idx = (idx + 1) % len(turn_order)
                # Skip NPCs for now by advancing until a player is found, or we could let a background task handle NPCs
                # For simplicity in this feature, let's just advance to the next player.
                # Actually, the prompt says "Players must wait their turn to act".
                # If we just advance the turn index in the database:
                from backend.database import CombatSession
                from sqlmodel import select
                loc_id = getattr(state, "current_location_id", "1")
                combat_session = session.exec(select(CombatSession).where(CombatSession.location_id == loc_id, CombatSession.is_active == True)).first()
                if combat_session:
                    
                    # Advance through NPCs and let the engine just generate a generic action for them?
                    # Or just advance the index.
                    combat_session.current_turn_index = idx
                    session.add(combat_session)
                    session.commit()
                    
        yield {
'''

content = re.sub(r'yield \{\s*"narration": narration,', replacement + r'\n            "narration": narration,', content)

with open('backend/engine.py', 'w') as f:
    f.write(content)

print("Updated backend/engine.py with turn advancement")
