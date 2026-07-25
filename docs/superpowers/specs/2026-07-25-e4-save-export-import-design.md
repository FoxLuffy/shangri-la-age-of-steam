# E4 — Save Export / Import Design

Roadmap item: **E4** (Save State Management). Depends on E2 (`SaveState`, snapshot shape).

## Goal
Let a player download their save as a JSON file and upload it back (same or another
character), with **schema validation** on import.

## Decisions (confirmed)
- **Export = the saved slot** (the character's existing `SaveState` snapshot). 404 if no
  save; the UI disables Export when none exists.
- **Import fills the slot** (validate → overwrite the character's `SaveState`). The live
  game is untouched until the player explicitly clicks **Load**.
- Leaves the legacy whole-DB `/export` `/import` endpoints alone.

## Schema (versioned, pydantic)
```python
class InventoryEntry(BaseModel):
    item_id: int
    quantity: int
    durability: Optional[int] = None

class QuestEntry(BaseModel):
    quest_id: int
    state: str

class SaveSnapshot(BaseModel):
    character: Dict[str, Any]
    world: Optional[Dict[str, Any]] = None
    inventory: List[InventoryEntry] = []
    quests: List[QuestEntry] = []

class SaveExport(BaseModel):
    schema_version: int = 1
    name: str
    created_at: str
    snapshot: SaveSnapshot
```

## Backend (`backend/routers/saves.py`)
- `GET /saves/{character_id}/export` → 404 if no slot; returns a `SaveExport`
  (schema_version, slot name/created_at, snapshot).
- `POST /saves/{character_id}/import` — body validated against `SaveExport`:
  - malformed body → FastAPI 422
  - `schema_version != 1` → 400
  - character not found → 404
  - success → upsert the character's `SaveState` with the payload's snapshot + name;
    return the save payload (`id/character_id/name/created_at`).

`CURRENT_SAVE_SCHEMA_VERSION = 1` constant. Import writes only to the target character's
slot; the snapshot's inner `character.id`/`user_id` are ignored on the later Load (E2).

## Frontend
- `api.ts`: `SaveExport` type + `exportSave(characterId)` (GET) and
  `importSave(characterId, payload)` (POST).
- `SaveManager.tsx` gains two buttons:
  - **Export** — disabled when no save; fetches `SaveExport`, downloads it as
    `saos-save-char{id}.json` via a Blob + object URL.
  - **Import** — hidden file input → read + `JSON.parse` → `window.confirm` overwrite →
    `importSave` → refresh metadata. Parse/validation errors surfaced in the existing
    error line.

## Out of scope
- Cross-schema migration, importing directly into live tables (Load handles that),
  multi-slot, encryption.

## Testing
- Backend (`backend/tests/test_save_state.py` additions):
  1. export returns `schema_version==1` + snapshot for a saved character.
  2. export 404 when the character has no save.
  3. import a valid payload → character's slot is populated (`GET /saves/{id}` returns it).
  4. import with `schema_version==99` → 400.
  5. import a malformed body (missing `snapshot`) → 422.
  6. import for an unknown character → 404.
- Frontend (`SaveManager.test.tsx` additions):
  - Export button disabled when no save.
  - Import: selecting a file calls `importSave` then refetches metadata.
  - Mock `URL.createObjectURL` / `URL.revokeObjectURL`.

## Acceptance
- Round-trip: export a save, delete it, import the file → slot restored; Load applies it.
- Import rejects bad schema/version with a clear status code.
- Full suites green plus new tests; `ruff` / `tsc` / `oxlint` clean.
