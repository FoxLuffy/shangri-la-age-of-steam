import re

with open('frontend/src/components/ChatInterface.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add combatState to ChatInterface
content = re.sub(
    r'const \[isMinigameActive, setIsMinigameActive\] = useState\(false\);',
    r'const [isMinigameActive, setIsMinigameActive] = useState(false);\n  const [combatState, setCombatState] = useState<any>(null);',
    content
)

# Update loadState to set combatState
content = re.sub(
    r'setIsMinigameActive\(\!\!data\.state\.active_minigame\);',
    r'setIsMinigameActive(!!data.state.active_minigame);\n        if (data.state.combat_state) {\n          setCombatState(data.state.combat_state);\n        } else {\n          setCombatState(null);\n        }',
    content
)

content = re.sub(
    r'import \{ useState, useEffect, useRef, type FormEvent \} from \'react\';',
    r"import { useState, useEffect, useRef, useMemo, type FormEvent } from 'react';",
    content
)

content = re.sub(
    r'const handleSendMessage = async \(e: FormEvent\) => \{',
    r'''const isMyTurn = useMemo(() => {
    if (!combatState || !combatState.is_active) return true;
    const { turn_order, current_turn_index } = combatState;
    if (!turn_order || current_turn_index >= turn_order.length) return true;
    const currentActor = turn_order[current_turn_index];
    return currentActor.type === 'player' && currentActor.id === player_;
  }, [combatState, characterId]);
  
  const currentTurnActor = combatState?.turn_order?.[combatState?.current_turn_index]?.name || '';
  
  const handleSendMessage = async (e: FormEvent) => {''',
    content
)

# Disable the form button
content = re.sub(
    r'<button\s*type="submit"\s*disabled=\{isLoading\}\s*className="bg-amber-600',
    r'<button type="submit" disabled={isLoading || !isMyTurn} className="bg-amber-600',
    content
)

content = re.sub(
    r'placeholder="What do you do\?"',
    r'placeholder={!isMyTurn ? Waiting for  to act... : "What do you do?"} disabled={!isMyTurn}',
    content
)

with open('frontend/src/components/ChatInterface.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated frontend/src/components/ChatInterface.tsx")
