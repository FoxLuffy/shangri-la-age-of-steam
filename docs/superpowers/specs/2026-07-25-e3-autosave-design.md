# E3 — Autosave & Checkpoints Design

Roadmap item: **E3** (Save State Management). Depends on E2 (endpoints) + E5 (`createSave`
api helper), both merged.

## Goal
Automatically keep the character's single save slot current, without the player having to
click "Save Now". Two triggers: **periodic** (every N player actions) and **pre-travel**
(before a fast-travel action).

## Decisions (confirmed)
- **One living save**: autosave and manual save both write the single per-character slot.
  The slot always reflects the latest checkpoint (roguelike-style; no save-scumming, no
  separate auto slot).
- **Frontend-driven**: triggers live in the client at discrete moments. No backend changes.
- **Periodic + pre-travel only**: no pre-combat checkpoint (combat is emergent from the
  narrative engine and unknown until after an action resolves). The periodic cadence covers
  combat indirectly.

## Module
`frontend/src/utils/autosave.ts` — isolated and dependency-injected for testing.

```ts
export const AUTOSAVE_EVERY = 5;
export function resetAutosaveCounter(): void;
export async function recordActionAndMaybeAutosave(
  characterId: number, save = createSave): Promise<boolean>;
export async function autosaveBeforeTravel(
  characterId: number, save = createSave): Promise<boolean>;
```

**Behavior**
- `recordActionAndMaybeAutosave`: increments an internal counter; on every `AUTOSAVE_EVERY`-th
  call, invokes `save(characterId)`. Returns whether a save fired.
- `autosaveBeforeTravel`: invokes `save(characterId)` once. Returns whether it succeeded.
- Both are **best-effort**: `save` errors are caught and swallowed (return `false`), never
  thrown — autosave must never block or crash gameplay.
- `resetAutosaveCounter`: zeroes the counter (call on new character/session).
- `save` defaults to E2/E5 `createSave` (POST /saves), which overwrites the single slot and
  preserves its existing name on overwrite.

## Integration (`frontend/src/components/ChatInterface.tsx`)
- After a successful player action submit → `recordActionAndMaybeAutosave(characterId)`.
- At the start of `handleTravel` → `await autosaveBeforeTravel(characterId)` before dispatching
  the travel action.
- Calls are fire-and-safe; failures are ignored.

## Out of scope
- Pre-combat checkpoints, backend hooks, autosave on/off UI toggle, multiple/auto slots,
  time-based cadence.

## Testing (`frontend/src/__tests__/utils/autosave.test.ts`)
Inject a mock `save`:
1. No save before the Nth action; save fires exactly on the Nth (5th) call.
2. `resetAutosaveCounter` restarts the cadence.
3. `autosaveBeforeTravel` calls `save` once with the character id.
4. A rejected `save` is swallowed (resolves `false`, no throw).

## Acceptance
- Periodic + pre-travel autosave write the single slot via `createSave`.
- Autosave never throws to the caller.
- Frontend suite stays green (65 baseline) plus new autosave tests; `tsc` + `oxlint` clean.
