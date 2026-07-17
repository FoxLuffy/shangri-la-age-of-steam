# Backend Foundation & API Setup Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Set up the FastAPI backend structure and a basic health check endpoint.

**Architecture:** A standard FastAPI structure with a `/health` endpoint to verify the server is running.

**Tech Stack:** Python, FastAPI, Uvicorn, Pytest

---

### Task 1: Initialize Backend Directory and Environment

**Objective:** Create the backend folder structure and a virtual environment.

**Files:**
- Create: `shangri-la-age-of-steam/backend/`
- Create: `shangri-la-age-of-steam/backend/main.py`
- Create: `shangri-la-age-of-steam/backend/requirements.txt`

**Step 1: Create directories and files**
Run: `mkdir -p shangri-la-age-of-steam/backend && touch shangri-la-age-of-steam/backend/main.py shangri-la-age-of-steam/backend/requirements.txt`

**Step 2: Populate requirements.txt**
Write to `shangri-la-age-of-steam/backend/requirements.txt`:
```text
fastapi
uvicorn
pytest
httpx
```

**Step 3: Commit changes**
```bash
git add backend/
git commit -m "chore: initialize backend structure"
```

---

### Task 2: Create Failing Health Check Test

**Objective:** Write a test that fails because the health check endpoint doesn't exist yet.

**Files:**
- Create: `shangri-la-age-of-steam/backend/tests/test_api.py`

**Step 1: Write failing test**
```python
from fastapi.testclient import TestClient
from fastapi import FastAPI

app = FastAPI()

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run test to verify failure**
Run: `pytest backend/tests/test_api.py -v`
Expected: FAIL — "ImportError" (because main.py isn't set up yet) or "404 Not Found"

---

### Task 3: Implement Minimal Health Check

**Objective:** Implement the basic FastAPI app and the `/health` endpoint.

**Files:**
- Modify: `shangri-la-age-of-steam/backend/main.py`

**Step 1: Write minimal implementation**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

**Step 2: Run test to verify pass**
Run: `pytest backend/tests/test_api.py -v`
Expected: PASS

**Step 3: Commit**
```bash
git add backend/
git commit -m "feat: add health check endpoint"
```
