# Persistent World State (Database Integration) Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Implement a persistent storage system using SQLite to save and load the game's world state.

**Architecture:** Use SQLAlchemy (via `sqlmodel`) to map our existing Pydantic models to a SQLite database. This will replace the current in-memory "dummy" state with a persistent one.

**Tech Stack:** Python, SQLAlchemy, SQLModel, SQLite

---

### Task 1: Initialize Database & Models

**Objective:** Set up the SQLAlchemy/SQLModel infrastructure and migrate existing models to database-compatible schemas.

**Files:**
- Create: `shangri-la-age-of-steam/backend/database.py`
- Modify: `shangri-la-age-of-steam/backend/models.py`

**Step 1: Create database utility**
Create `database.py` with `SessionLocal` and `engine` setup for SQLite.

**Step 2: Update models for SQLAlchemy**
Modify `models.py` to inherit from `SQLModel` (or `SQLAlchemy` models) so they can be persisted.
*Note: We'll need to handle the 1-to-many relationship between Location and NPCs.*

**Step 3: Verify migrations**
Run a script to create the tables in `saos.db`.

**Step 4: Commit**
```bash
git add backend/
git commit -m "feat: add database models and initialization"
```

---

### Task 2: Create Persistence Test

**Objective:** Write a test to verify that a state can be saved to and retrieved from the database.

**Files:**
- Create: `shangri-la-age-of-steam/backend/tests/test_persistence.py`

**Step 1: Write test**
Create a test that:
1. Inserts a mock `WorldState` (Location + NPCs).
2. Queries the database.
3. Asserts equality.

**Step 2: Run test**
Run: `pytest backend/tests/test_persistence.py -v`

**Step 3: Commit**
```bash
git add backend/
git commit -m "test: add persistence verification"
```

---

### Task 3: Implement State Repository

**Objective:** Create a Repository pattern to handle CRUD operations for the game state.

**Files:**
- Create: `shangri-la-age-of-steam/backend/repository.py`

**Step 1: Implement Repository**
Create a class that provides methods like `get_latest_state()`, `save_state(WorldState)`, and `update_location(id, data)`.

**Step 2: Integrate with NarrativeEngine**
Modify `NarrativeEngine` to use the `StateRepository` instead of just passing a `WorldState` object.

**Step 3: Verify with Integration Test**
Verify that a request to `/chat` correctly updates the database.

**Step 4: Commit**
```bash
git add backend/
git commit -m "feat: implement state repository"
```
