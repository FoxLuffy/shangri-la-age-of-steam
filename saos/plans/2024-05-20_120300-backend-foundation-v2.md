# Core State Model & vLLM Integration Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Define the world state model and create a basic client to interact with a vLLM backend.

**Architecture:** Use Pydantic models to define a schema for the World State (locations, NPCs, current event). Create a client class to handle structured requests to a vLLM endpoint.

**Tech Stack:** Python, Pydantic, HTTPX, OpenAI-compatible library (for vLLM)

---

### Task 1: Define World State Schema

**Objective:** Create a Pydantic model to represent the game's state.

**Files:**
- Create: `shangri-la-age-of-steam/backend/models.py`
- Modify: `shangri-la-age-of-steam/backend/requirements.txt` (Add `pydantic`)

**Step 1: Update requirements.txt**
Append `pydantic` and `openai` (standard for vLLM) to `backend/requirements.txt`.

**Step 2: Write Pydantic models**
Write to `backend/models.py`:
```python
from pydantic import BaseModel
from typing import List, Optional

class Location(BaseModel):
    id: str
    name: str
    description: str
    npcs: List[str]

class NPC(BaseModel):
    id: str
    name: str
    traits: List[str]
    current_dialogue: Optional[str] = None

class WorldState(BaseModel):
    current_location: Location
    active_npcs: List[NPC]
    global_event: Optional[str] = None
```

**Step 3: Verify with a script**
Create a temporary script `backend/verify_models.py` that instantiates a `WorldState` and prints it.

**Step 4: Commit**
```bash
git add backend/
git commit -m "feat: add pydantic models for world state"
```

---

### Task 2: Create Failing vLLM Connectivity Test

**Objective:** Write a test that fails because the vLLM client is not configured or the server is unreachable.

**Files:**
- Create: `shangri-la-age-of-steam/backend/tests/test_vllm_client.py`

**Step 1: Write failing test**
```python
import pytest
from backend.client import VLLMClient

def test_vllm_connection():
    # This will fail because client is uninitialized
    client = VLLMClient(api_base="http://localhost:8000/v1")
    response = client.generate("Hello")
    assert response.status_code == 200
```

**Step 2: Run test to verify failure**
Run: `pytest backend/tests/test_vllm_client.py -v`
Expected: FAIL — "ImportError" or "ConnectionError"

---

### Task 3: Implement vLLM Client Wrapper

**Objective:** Create a client to interact with a vLLM-compatible API.

**Files:**
- Create: `shangri-la-age-of-steam/backend/client.py`

**Step 1: Write minimal implementation**
```python
import httpx
from typing import Dict, Any

class VLLMClient:
    def __init__(self, api_base: str):
        self.api_base = api_base
        self.headers = {"Authorization": "Bearer-NONE"}

    def generate(self, prompt: str) -> Dict[str, Any]:
        with httpx.Client() as client:
            response = client.post(
                f"{self.api_base}/completions",
                json={"model": "default", "prompt": prompt},
                headers=self.headers
            )
            return response.json()
```

**Step 2: Run test to verify pass (mocked or local)**
(Note: For the actual test, we will use a mock to simulate the 200 OK response to keep the test independent of actual networking.)

**Step 3: Commit**
```bash
git add backend/
git commit -m "feat: add vLLM client wrapper"
```
