# vLLM Prompt Engineering & State Update Logic Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Implement the logic that constructs prompts for the vLLM backend and updates the WorldState based on the AI's narrative output.

**Architecture:** The `NarrativeEngine` will use a `PromptBuilder` to format the `WorldState` and `PlayerAction` into a structured prompt. It will then call `VLLMClient` and parse the result into a `NarrativeResult`, updating the `WorldState` in the process.

**Tech Stack:** Python, Pydantic, httpx

---

### Task 1: Create Prompt Builder & Result Parser

**Objective:** Create a utility to construct the prompt and parse the response into the correct schemas.

**Files:**
- Create: `shangri-la-age-of-steam/backend/prompt_utils.py`
- Modify: `shangri-la-age-of-steam/backend/models.py` (Add `Prompt` and `RawResponse` types)

**Step 1: Add internal types to `models.py`**
```python
class Prompt(BaseModel):
    system_prompt: str
    user_content: str

class RawResponse(BaseModel):
    text: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
```

**Step 2: Implement Prompt Builder**
Create `prompt_utils.py` with a function to generate a structured prompt.
```python
def build_narrative_prompt(state: WorldState, action: PlayerAction) -> str:
    return f"""
    World State: {state.current_location.description}
    Current Action: {action.action_text}
    
    Generate a narrative description of what happens next.
    """
```

**Step 3: Commit**
```bash
git add backend/
git commit -m "feat: add prompt builder and internal types"
```

---

### Task 2: Create Failing Test for Narrative Processing

**Objective:** Write a test that fails because `NarrativeEngine` doesn't yet actually call the vLLM backend.

**Files:**
- Create: `shangri-la-age-of-steam/backend/tests/test_narrative_flow.py`

**Step 1: Write failing test**
```python
import pytest
from unittest.mock import MagicMock
from backend.engine import NarrativeEngine
from backend.models import WorldState, Location, PlayerAction
from backend.client import VLLMClient

def test_narrative_engine_vllm_call():
    loc = Location(id="1", name="Forest", description="Forest", npcs=[])
    state = WorldState(current_location=loc, active_npcs=[])
    
    # Mock the client
    mock_client = MagicMock(spec=VLLMClient)
    mock_client.generate.return_value = {"text": "The trees rustle."}
    
    engine = NarrativeEngine(state, vllm_client=mock_client)
    action = PlayerAction(action_text="Look around", current_location_id="1")
    
    result = engine.process_action(action)
    assert "trees rustle" in result.narration.lower()
```

**Step 2: Run test to verify failure**
Run: `pytest backend/tests/test_narrative_flow.py -v`
Expected: FAIL (because engine.py still has placeholder logic)

---

### Task 3: Implement vLLM Logic in NarrativeEngine

**Objective:** Wire the `NarrativeEngine` to use the `PromptBuilder` and `VLLMClient`.

**Files:**
- Modify: `shangri-la-age-of-steam/backend/engine.py`

**Step 1: Update `process_action`**
Update the engine to:
1. Build prompt using `prompt_utils`.
2. Call `vllm_client.generate()`.
3. Parse result.
4. Update `state.current_location` if location changed.

**Step 2: Run test to verify pass**
Run: `pytest backend/tests/test_narrative_flow.py -v`
Expected: PASS

**Step 3: Commit**
```bash
git add backend/
git commit -m "feat: connect narrative engine to vLLm client"
```
