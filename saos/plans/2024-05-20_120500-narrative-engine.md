# Narrative Engine & State Update Logic Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Create the core logic to process player input, generate AI responses via vLLM, and update the world state.

**Architecture:** An `Engine` class that takes a `PlayerAction`, fetches context from the `WorldState`, calls the `VLLMClient`, and produces a `NarrativeResult` (text + state changes).

**Tech Stack:** Python, Pydantic, httpx

---

### Task 1: Define Input/Output Models

**Objective:** Create Pydantic models for player actions and the narrative results.

**Files:**
- Create: `shangri-la-age-of-steam/backend/models.py` (Modify to add new models)
- Create: `shangri-la-age-of-steam/backend/requirements.txt` (Ensure pydantic is present)

**Step 1: Add models to `backend/models.py`**
```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# ... existing models (Location, NPC, WorldState) ...

class PlayerAction(BaseModel):
    action_text: str
    current_location_id: str

class NarrativeResult(BaseModel):
    narration: str
    state_updates: Optional[Dict[str, Any]] = None
    active_npcs: List[str]
```

**Step 2: Verify models**
Create `backend/verify_models.py` to test instantiation of `PlayerAction` and `NarrativeResult`.

**Step 3: Commit**
```bash
git add backend/
git commit -m "feat: add input and output models"
```

---

### Task 2: Create Failing Narrative Engine Test

**Objective:** Write a test that fails because the `NarrativeEngine` is not implemented.

**Files:**
- Create: `shangri-la-age-of-steam/backend/tests/test_engine.py`

**Step 1: Write failing test**
```python
import pytest
from backend.engine import NarrativeEngine
from backend.models import WorldState, Location

def test_narrative_engine_processing():
    # Setup dummy state
    loc = Location(id="1", name="Forest", description="A dark forest", npcs=["Orc"])
    state = WorldState(current_location=loc, active_npcs=[])
    
    engine = NarrativeEngine(state)
    action = PlayerAction(action_text="I walk into the forest", current_location_id="1")
    
    result = engine.process_action(action)
    assert "forest" in result.narration.lower()
```

**Step 2: Run test to verify failure**
Run: `pytest backend/tests/test_engine.py -v`
Expected: FAIL — "ImportError: cannot import name 'NarrativeEngine' from 'backend.engine'"

---

### Task 3: Implement Narrative Engine Skeleton

**Objective:** Create the `NarrativeEngine` class with the core `process_action` method.

**Files:**
- Create: `shangri-la-age-of-steam/backend/engine.py`

**Step 1: Write minimal implementation**
```python
from backend.models import WorldState, PlayerAction, NarrativeResult
from backend.client import VLLMClient

class NarrativeEngine:
    def __init__(self, state: WorldState, vllm_client: VLLMClient):
        self.state = state
        self.vllm_client = vllm_client

    def process_action(self, action: PlayerAction) -> NarrativeResult:
        # Placeholder for actual vLLM logic
        return NarrativeResult(
            narration="You entered the forest.",
            active_npcs=self.state.active_npcs
        )
```

**Step 2: Run test to verify pass**
(Note: Update `test_engine.py` to provide a mock/dummy `VLLMClient`)
Run: `pytest backend/tests/test_engine.py -v`
Expected: PASS

**Step 3: Commit**
```bash
git add backend/
git commit -m "feat: implement narrative engine skeleton"
```
