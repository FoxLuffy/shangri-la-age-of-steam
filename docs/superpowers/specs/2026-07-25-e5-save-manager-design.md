# E5 — SaveManager UI Design

Roadmap item: **E5** (Save State Management). Depends on E2 (shipped: single-slot
save/load/delete endpoints keyed by `character_id`).

## Goal
Give the player an in-game UI to manage their single save slot: **Save**, **Load**,
and **Delete**, with confirmation on destructive actions (Load, Delete).

## Scope
- In scope: Save (create/overwrite), Load (restore), Delete. All inside the in-game
  `SettingsMenu` modal via a new `SaveManager.tsx` section.
- Out of scope: rename, export/import (roadmap E4), autosave (roadmap E3), any lobby
  or character-select entry point.

## Placement rationale
The app auto-resumes the last character from `localStorage` (`App.tsx`), and
`SessionLobby` runs before any character exists — so a lobby "Load" has no character
context. `SettingsMenu` already receives `character` + `onUpdateCharacter` + `onClose`,
making it the correct home for all three actions.

## Component
`frontend/src/components/SaveManager.tsx`

**Props**
- `characterId: number`
- `onLoad: () => void` — called after a successful restore.

**State**
- `save: SaveMeta | null` — current slot metadata (null = no save yet).
- `loading: boolean`, `error: string | null`.

**Behavior**
- On mount: `getSave(characterId)`. On 404 (or reject) → `save = null` ("No save yet").
  On success → store metadata (name + created_at).
- **Save Now**: `createSave(characterId)` → refetch metadata. No confirmation.
- **Load**: `window.confirm(...)` warning it overwrites current progress → `loadSave(characterId)`
  → `onLoad()`. Disabled when `save === null`.
- **Delete**: `window.confirm(...)` → `deleteSave(characterId)` → `save = null`. Disabled when
  `save === null`.

**Why `onLoad` triggers a full reload**
Loading restores character + global world + inventory + quests in the DB. `SettingsMenu`
holds only `character`, not `worldState`. `SettingsMenu` passes
`onLoad={() => window.location.reload()}` so all state re-fetches from the restored DB.
`SaveManager` itself only calls the `onLoad` prop, keeping it unit-testable.

## API client additions (`frontend/src/api.ts`)
```ts
export interface SaveMeta {
  id: number;
  character_id: number;
  name: string;
  created_at: string;
}
export const createSave = (characterId, name?) => POST /saves {character_id, name}
export const getSave    = (characterId)       => GET  /saves/{characterId}
export const loadSave   = (characterId)       => GET  /saves/{characterId}/load
export const deleteSave = (characterId)       => DELETE /saves/{characterId}
```

## SettingsMenu integration
Render `<SaveManager characterId={character.id} onLoad={() => window.location.reload()} />`
as a new section block, styled to match existing amber/slate section cards.

## Testing (`frontend/src/__tests__/components/SaveManager.test.tsx`)
Mock `../../api` (MarketUI test pattern). Stub `window.confirm`.
1. Renders; shows "No save yet" when `getSave` rejects.
2. Shows slot name/timestamp when `getSave` resolves.
3. Save Now → calls `createSave`, then refetches metadata.
4. Load with `confirm → true` → calls `loadSave` + `onLoad`.
5. Load with `confirm → false` → neither called.
6. Delete with `confirm → true` → calls `deleteSave`; Load/Delete disabled when no save.

## Acceptance
- All three actions work against the E2 endpoints.
- Destructive actions (Load, Delete) confirm first.
- Frontend suite stays green (58 baseline) plus new SaveManager tests; `tsc --noEmit`
  and `oxlint` clean.
