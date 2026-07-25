# E1 — Session Save Metadata Design

Roadmap item: **E1** (Save State Management). Depends on E2 (`SaveState` model), merged.

## Goal
Surface per-character save info in the session list so a returning player can see, for
each character, **when it was last saved** and **where it is**.

## Decisions (confirmed)
- **Enrich the existing `GET /sessions/{user_id}`** response rather than add an endpoint.
  Backward-compatible: existing keys (`id`, `name`, `character_class`, ...) remain.
- `last_saved` = the character's `SaveState.created_at` (null if never saved).
- `location_name` = the character's **current** `location_id` resolved via the `Location`
  table (null if unresolved).

## Backend (`backend/repository.py`)
Change `StateRepository.get_sessions` to return a list of dicts:
```python
character.model_dump()  # all existing character fields
+ "last_saved": SaveState.created_at | None
+ "has_save": bool
+ "location_name": Location.name | None   # from character.location_id
```
Only consumer is the `/sessions/{user_id}` endpoint, which already returns whatever
`get_sessions` yields. No API-shape break for existing keys.

## Frontend
- `Character` type (`api.ts`) gains optional `last_saved?: string | null`,
  `has_save?: boolean`, `location_name?: string | null`.
- `CharacterCreation.tsx` session card adds a line under the class:
  `location_name` + `Saved: <localized time>` when `has_save`, else `No save yet`.

## Out of scope
- New endpoint, snapshot-derived location, playtime, save preview thumbnails.

## Testing
- Backend (`backend/tests/test_save_state.py` additions):
  1. A character with a save → `/sessions/{user_id}` item has `has_save:true`,
     `last_saved` non-null, `location_name` resolved.
  2. A character with no save → `has_save:false`, `last_saved:null`, `location_name`
     still resolved from current location.
- Frontend (`CharacterCreation.test.tsx` addition):
  - Session card renders `location_name` and the saved time when metadata is present.

## Acceptance
- `/sessions/{user_id}` returns the three extra fields per character; existing keys intact.
- Session cards show location + last-saved (or "No save yet").
- Full suites stay green plus new tests; `tsc` + `oxlint` clean.
