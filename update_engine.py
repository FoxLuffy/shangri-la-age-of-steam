import re

with open('backend/engine.py', 'r') as f:
    engine_content = f.read()

# Add a check before hitting the LLM in process_action
turn_check = '''
        if session and state.is_combat_active and state.combat_state:
            cs = state.combat_state
            turn_order = cs.get("turn_order", [])
            idx = cs.get("current_turn_index", 0)
            if turn_order and idx < len(turn_order):
                current_turn = turn_order[idx]
                if current_turn["type"] == "player" and current_turn["id"] != f"player_{action.character_id}":
                    # NOT THIS PLAYER'S TURN
                    yield {
                        "narration": f"[System] It is not your turn! It is currently {current_turn['name']}'s turn.",
                        "state_updates": {},
                        "events": [],
                        "is_combat_active": True
                    }
                    return
'''

engine_content = re.sub(
    r'(def process_action\(self, action: PlayerAction, session: Optional\[Session\] = None\):.*?ghost_echoes = \[\])',
    r'\1' + turn_check,
    engine_content,
    flags=re.DOTALL
)

with open('backend/engine.py', 'w') as f:
    f.write(engine_content)

print("Updated backend/engine.py with turn check")
