import { createSave } from '../api';

/** Autosave the character's single save slot every Nth player action. */
export const AUTOSAVE_EVERY = 5;

type SaveFn = (characterId: number, name?: string) => Promise<unknown>;

let actionCount = 0;

/** Reset the periodic-autosave counter (call on a new character/session). */
export function resetAutosaveCounter(): void {
  actionCount = 0;
}

async function trySave(characterId: number, save: SaveFn): Promise<boolean> {
  try {
    await save(characterId);
    return true;
  } catch {
    // Autosave is best-effort: never block or crash gameplay on failure.
    return false;
  }
}

/**
 * Record a player action; autosave on every AUTOSAVE_EVERY-th call.
 * Returns whether a save fired.
 */
export async function recordActionAndMaybeAutosave(
  characterId: number,
  save: SaveFn = createSave,
): Promise<boolean> {
  actionCount += 1;
  if (actionCount % AUTOSAVE_EVERY !== 0) {
    return false;
  }
  return trySave(characterId, save);
}

/** Autosave immediately before a travel action. Returns whether it succeeded. */
export async function autosaveBeforeTravel(
  characterId: number,
  save: SaveFn = createSave,
): Promise<boolean> {
  return trySave(characterId, save);
}
