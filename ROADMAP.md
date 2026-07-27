# 🗺 ROADMAP — Shangri-La: Age of Steam

Post-playtest backlog (2026-07-27). Derived from 11 community reports + a 22-turn demo
playtest — see `docs/playtest-2026-07-27.md` for evidence. The previous roadmap shipped
42/42 and is archived at `docs/roadmap-completed-2026-07.md`.

Each item is targetable by `saosgo <ID>`: it has a goal, acceptance criteria, and is
testable. Work one chunk at a time, most-severe first.

Status legend: [COMPLETE] [PARTIAL] [BROKEN] [NOT STARTED]

> Test baseline: **168 backend** (run `pytest` from repo ROOT — `backend/` cwd breaks
> imports), **97 frontend** (Vitest). Keep both green.

Severity: **P0** = broken/regression, fix first · **P1** = major gap · **P2** = polish.

---

## Chunk A — Combat (P0/P1) · reports #11 + playtest

- **A1 [COMPLETE] (P0) Stop combat leaking into new characters.**
  Goal: a freshly created character never spawns with `is_combat_active=True`.
  Root cause: global `WorldState.is_combat_active` is read for a new character instead of
  per-character combat state. Acceptance: create a character while another world row has
  combat active → new character's `/state.is_combat_active` is False and no `CombatSession`
  is attached; backend test.

- **A2 [COMPLETE] (P0) Reject placeholder enemy names in combat.**
  Goal: `combat_updates.enemy` values like `"none"`, `"unknown"`, `"unknown enemy"`, `""`
  never instantiate an NPC. Root cause: #179 combat-fidelity creates a hostile NPC from any
  `enemy` string (observed: an NPC literally named "none"). Acceptance: `apply_combat_update`
  with `enemy` in the placeholder set adds no NPC/participant; existing junk NPCs named
  "none"/"Unknown Enemy" are cleaned up (migration or guard on read); backend test.

- **A3 [NOT STARTED] (P1) Give combat real mechanical stakes.**
  Goal: attacks change HP. Currently `player_updates.hp_change` is always 0 and enemies have
  no HP resolution. Acceptance: the extraction/combat path applies non-zero `hp_change` to
  player and/or enemy per exchange, enemy HP reaches 0 to end the fight, and defeat/victory is
  reflected in `/state`; backend test with a scripted exchange.

- **A4 [NOT STARTED] (P1) Dedicated combat pane + isolated combat chat (frontend).**
  Goal: combat opens its own pane like the minigame, with a separate input; the main chat is
  intentionally paused (not "locked out" with mis-placed health bars); on resolution a summary
  is posted back into the main narrative context. Acceptance: when `is_combat_active` becomes
  true the combat pane mounts with correctly-placed health bars, main chat shows a "in combat"
  state, and end-of-combat writes a result line to the main log; frontend test + screenshot.

## Chunk B — Movement & world simulation (P0/P1) · reports #3, #10, #4

- **B1 [COMPLETE] (P0) Travel reflects in the UI.**
  Goal: travelling (map/travel control) updates the top bar location AND the Environment pane,
  and swaps the location's NPCs — no NPC "stuck" from the previous location. Backend travel is
  correct (verified 4→1); this is a frontend state-sync bug. Acceptance: driving a travel in
  the UI changes the displayed location + NPC list to match `/state`; frontend test asserting
  the pane re-renders on `current_location_id` change.

- **B2 [COMPLETE] (P1) World ticks are turn-gated.**
  Goal: the world only ticks as a possible consequence of a chat turn — never on a background
  timer. Report #10: random ticks inject phantom "overheard" NPCs that aren't present.
  Acceptance: no world-time/NPC mutation occurs without a `/chat` turn; a tick may fire at most
  once per turn and never adds NPCs absent from the current location; backend test.

- **B3 [COMPLETE] (P1) Location-aware NPC instantiation + de-clutter.**
  Goal: when the narration names a character, instantiate them at the correct location and only
  surface NPCs actually at the player's location; cap runaway `active_npcs` growth (playtest saw
  5+ pile up). Ties into #4. Acceptance: mentioning a character adds them to that location's NPCs
  (not a global soup); `/state.active_npcs` only lists current-location NPCs; backend test.

## Chunk C — Side content visibility (P1) · reports #7, #8, #9

- **C1 [COMPLETE] (P1) Bounty system: single active bounty + visible + LLM-aware.**
  Goal: the player can view their active bounty; only ONE bounty active at a time; the narrative
  prompt weaves hints/references to it. Report #8 (bounties invisible; today they leak into the
  QUESTS list). Acceptance: a Bounties view shows the one active bounty and its progress;
  accepting a second is blocked while one is active; the prompt includes the active bounty;
  backend test for the single-active rule + frontend view test.

- **C2 [COMPLETE] (P1) Populate the Explorer's Journal.**
  Goal: the journal accumulates discoveries (locations visited, NPCs met, lore found) instead of
  staying empty (#7). Acceptance: after visiting a location / meeting an NPC, `/state` (or a
  journal endpoint) returns non-empty journal entries and the UI renders them; backend + frontend test.

- **C3 [NOT STARTED] (P2) Guild view refresh after creation.**
  Goal: creating a guild immediately shows it — no "close and reopen" that shows the same screen
  (#9). Acceptance: after guild creation the guild view reflects the new guild without a manual
  reload; frontend test.

## Chunk D — NPC interaction polish (P2) · reports #1, #6

- **D1 [NOT STARTED] (P2) Fix or remove the "Show Dialogue" control.**
  Goal: the Active-NPC "Show Dialogue" button shows meaningful, updating dialogue, or is removed
  (#6). Acceptance: expanding it shows the NPC's current line and it updates across turns; or the
  control is gone; frontend test.

- **D2 [NOT STARTED] (P2) Eavesdrop / overhear nearby (not-engaged) NPCs.**
  Goal: let the player overhear NPCs who are present-but-not-engaged (the "Nearby" earshot group),
  answering report #1's first half. Acceptance: an "eavesdrop/listen" action surfaces snippets
  from Nearby NPCs without engaging them (they stay `in_earshot=False`); backend test. Builds on
  the earshot feature (#179/#180).

## Chunk E — Frontend audio (P2) · report #2

- **E1 [NOT STARTED] (P2) Stop the audio toggle flicker.**
  Goal: with audio enabled it stays on — no repeated ~half-second on/off flicker (#2). Acceptance:
  the audio-enabled state is stable across renders/turns (no effect re-running the toggle);
  frontend test or documented root-cause fix.

---

## Suggested order
A1 → A2 (P0 combat regressions, quick) → B1 (travel UI, high user impact) → A3/A4 (combat depth
+ pane) → B2/B3 (world sim) → C1/C2 (bounty + journal) → C3/D1/D2/E1 (polish).
