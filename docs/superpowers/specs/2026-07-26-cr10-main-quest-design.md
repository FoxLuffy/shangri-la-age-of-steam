# CR10 — Main Quest at Character Creation (staged) Design

Report #3: choose / random / LLM-generate a main quest at creation; it drives a longer,
**staged** arc.

## Model (`backend/database.py`)
```python
class MainQuest(SQLModel, table=True):
    id, character_id (FK, unique), title, description,
    stages: List[Dict] (JSON) — [{ "description": str, "status": "pending|active|done" }],
    current_stage: int = 0, status: str = "active"
```
One per character. `current_stage` indexes the active stage. + Alembic migration.

## Presets & generation (`backend/main_quests.py`)
- `PRESET_MAIN_QUESTS`: 3–4 curated arcs, each `{id, title, description, stages: [str,...]}`.
- `preset_list()` → presets for the picker.
- `random_preset()` → a random preset.
- `stages_from_titles(list[str])` → `[{description, status}]` with stage 0 active.
- `generate_main_quest(client, preset, origin, backstory)` → `{title, description, stages}`
  from the LLM; on any error/parse failure, **fall back to a random preset**.

## Endpoints (`backend/main.py`)
- `GET /main-quests` → `preset_list()`.
- `POST /main-quests/generate {preset, origin, backstory}` → generated quest (or preset fallback).
- `GET /main-quest/{character_id}` → the character's MainQuest (title/description/stages/
  current_stage/current objective) or 404.
- `create_character`: `CharacterCreateRequest.main_quest: Optional[MainQuestInput]`
  (`{title, description, stages: [str]}`). If present, create the MainQuest (stage 0 active,
  rest pending).

## Engine + prompt
- `state_updates.main_quest_updates` (e.g. `{ "advance_stage": true }`): mark the current
  stage `done` and activate the next; when the last completes, `status = "completed"`.
  Applied in `engine.process_action`.
- `narrative_prompt.j2`: render the **current main-quest objective** and instruct the
  narrator to advance it (emit `main_quest_updates.advance_stage`) when the player completes it.

## Frontend
- `api.ts`: `MainQuestPreset`/`MainQuestInput` types + `fetchMainQuests`, `generateMainQuest`,
  `fetchMainQuest`.
- `CharacterCreation`: a "Main Quest" step — **None / Preset / Random / Generate**, with a
  stages preview; the chosen `{title, description, stages}` is passed to `createCharacter`.
- Compact in-game readout of the current objective via `GET /main-quest` (a small component
  in the Journal/Dossier area).

## Tests
- Backend: presets have stages; `generate_main_quest` parses a mocked LLM response and
  falls back to a preset on error; `create_character` attaches a MainQuest (stage 0 active);
  `GET /main-quest/{id}` returns progress; engine `advance_stage` moves the pointer + marks
  done + completes at the end; prompt renders the current objective.
- Frontend: picker renders; Random selects a preset; Generate calls the API; the selection
  flows into `createCharacter`; the readout shows the current objective.

## Out of scope
- Branching stages, per-stage rewards/mechanics, editing the arc mid-game.

## Acceptance
- A player can pick/roll/generate a staged main quest at creation; it persists, appears in
  play (prompt + readout), and advances stage-by-stage via `main_quest_updates`.
