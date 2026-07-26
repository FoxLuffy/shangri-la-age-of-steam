# 🛠 Community Bug Roadmap — Shangri-La: Age of Steam

Sourced from the deployed server's user reports (`GET /admin/bugreports`,
retrieved 2026-07-26). 6 reports, all bugs, all `open`. Ranked highest priority first.
Each item has a stable ID (`CR#`) targetable by a fix flow / `saosgo`.

Status legend: [OPEN] [IN PROGRESS] [FIXED]

> Regenerate this file with the `saos-reports` skill (non-destructive fetch).

---

## CR1 — [FIXED] WebSocket `/ws` returns 404 on the deployed server
**Reports:** #5 · **Severity:** High (breaks real-time sync; likely aggravates CR4)

Backend logs: `WARNING: No supported WebSocket library detected ... GET /ws HTTP/1.1 404
Not Found`. `backend/requirements.txt` pins bare `uvicorn` — no ASGI WebSocket backend, so
uvicorn can't accept the `/ws` upgrade and returns 404.

**Cause:** missing `uvicorn[standard]` (or `websockets`/`wsproto`) dependency in the deploy image.
**Fix:** change `uvicorn` → `uvicorn[standard]` in `backend/requirements.txt` (or add
`websockets`); rebuild/redeploy the backend image.
**Acceptance:** `/ws` upgrades succeed (101, not 404); the frontend WebSocketSync connects;
no "Unsupported upgrade request" warnings in logs.

## CR2 — [FIXED] Bounty board crashes: `Unexpected token '<' … is not valid JSON`
**Reports:** #4 · **Severity:** High (feature unusable)

`BountyBoard.tsx` calls `fetch('/api/gameplay/bounties?...')` — a raw relative path with an
`/api` prefix — instead of the shared `api` axios client (`BACKEND_URL`). In production that
path isn't proxied to the backend, so it returns `index.html` (`<!doctype …>`); `res.json()`
then throws the reported error. Backend route exists at `GET /gameplay/bounties`.

**Cause:** wrong fetch path/client in `frontend/src/components/BountyBoard.tsx`
(both `/bounties` and `/bounties/accept`).
**Fix:** use the `api` client / `BACKEND_URL` with the correct `/gameplay/bounties` path
(add helpers in `api.ts`); handle non-OK responses gracefully.
**Acceptance:** bounty board loads real bounties (or a clean empty state) in prod; Accept
works; no JSON-parse error.

## CR3 — [FIXED] "Start minigame" does nothing
**Reports:** #1 · **Severity:** High (feature broken)

Clicking start yields no visible effect. `MinigamePanel` only renders when
`worldState.active_minigame` is set (`App.tsx`), so if the start action never creates/returns
an active minigame (or `/minigames/start` isn't invoked / isn't reflected in `/state`), the
panel never opens.

**Cause (to confirm):** the start-minigame trigger doesn't persist/surface an
`active_minigame` in world state, or the button isn't wired to `/minigames/start`.
**Fix:** trace the start path (button → API → `active_minigame` in `/state` → panel);
ensure a minigame is created and the panel opens.
**Acceptance:** starting a minigame opens the MinigamePanel with a playable puzzle.

## CR4 — [FIXED] NPCs missing from the Environment overview
**Reports:** #3, #6 (grouped — same panel) · **Severity:** Medium-High (core UX regression)

- #3: after a dynamic world event, **all** NPCs disappear from the Environment overview.
- #6: NPCs the player is **currently in conversation with** don't appear there either.

The panel renders `worldState.state.active_npcs` (`ChatInterface` → gameStore). Active NPCs
are computed per-location in `repository.get_latest_state`; a world tick / dynamic event may
move NPCs or clear `active_npcs_ids`, and conversation partners aren't guaranteed to be in
the location set.

**Cause (to confirm):** world-simulation/event side effects drop NPCs from the active set;
active-NPC selection doesn't include conversation partners.
**Fix:** keep location NPCs present across events, and include the player's
conversation/target NPCs in `active_npcs`.
**Acceptance:** NPCs remain listed through world events; anyone the player is talking to
shows in the Environment overview.

## CR5 — [FIXED] Dynamic events dump raw/unclear data (immersion-breaking)
**Reports:** #2 · **Severity:** Low-Medium (polish)

The dynamic-events feed shows a lot of raw data whose meaning is unclear. It should surface
**only meaningful changes**, phrased in-world rather than as data.

**Cause:** event/state-update rendering prints raw payloads instead of a curated,
human-readable summary.
**Fix:** render dynamic events as concise, in-world highlights (diff of what changed);
suppress noisy/raw fields.
**Acceptance:** events read as short immersive notices; no raw JSON/state dumps in the feed.

---

### Source reports
| CR | Report ids | Type | Reported |
|----|-----------|------|----------|
| CR1 | #5 | bug | 2026-07-26 |
| CR2 | #4 | bug | 2026-07-26 |
| CR3 | #1 | bug | 2026-07-26 |
| CR4 | #3, #6 | bug | 2026-07-26 |
| CR5 | #2 | bug | 2026-07-26 |

---

# Round 2 — 2026-07-26 (fetched + cleared from prod)

5 new reports (2 bugs, 3 features). To be validated/expanded during the `play-session`
playtest, then prioritized for implementation. Highest priority first.

## CR6 — [RESOLVED via CR11] Narrator lacks per-turn context → inaccurate narrative
**Reports:** #5 (bug) · **Severity:** High (core narrative quality)

"It seems as if vLLM does not have the context of every turn. This makes it hard to create
an accurate narrative." The prompt likely doesn't include enough recent history
(prior turns / world & NPC memories), so continuity breaks.
**Area:** `narrative_prompt.j2`, `engine.process_action` context assembly, `world_memories`
/ NPC `memories` inclusion, and the per-turn history window sent to the model.
**Acceptance:** narration reflects recent turns (names, events, choices) consistently across
a multi-turn session.

## CR7 — [OPEN] Map accumulates duplicate locations
**Reports:** #2 (bug) · **Severity:** High (world integrity)

"The map is getting increasingly more duplicate locations." Something creates locations
repeatedly (e.g. a state-update/exploration path or seed/migration re-running) without
dedup by id/name.
**Area:** `repository.update_location` / location creation on `state_updates`, exploration
new-area handling, `seed_data`. Dedup by id/name; don't recreate existing.
**Acceptance:** exploring/playing doesn't spawn duplicate locations; the map/all_locations
stays clean.

## CR8 — [OPEN] Narrator should steer/lead, not just describe
**Reports:** #4 (feature) · **Severity:** Medium (prompt/design)

"Narrator should try to steer the narrative more. Not just describe, but lead." Add
prompt guidance to offer hooks, stakes, and forward momentum (goals, threats, choices)
rather than passive description.
**Area:** `narrative_prompt.j2` system/style guidance.
**Acceptance:** narration proposes direction/stakes and nudges the player toward action.

## CR9 — [OPEN] Vary the starting location
**Reports:** #1 (feature) · **Severity:** Low-Medium

"Not always the same starting location." New characters should start in one of several
locations (random, or tied to origin/class) instead of a fixed default.
**Area:** `create_character` initial `location_id`; optionally map to origin background.
**Acceptance:** new characters can begin in different starting locations.

## CR10 — [OPEN] Main quest at character creation (choose / random / generate)
**Reports:** #3 (feature) · **Severity:** Large arc (design + dev)

During character creation, let the player pick a main quest, roll a random one, or request
a generated one. Explicitly a long development + story arc.
**Area:** character-creation UI + a quest/main-arc model + generation; multi-phase.
**Acceptance:** (to be scoped) a main quest can be selected/generated at creation and drives
a longer narrative arc. Likely split into sub-items after playtest + design.

### Round 2 source reports
| CR | Report id | Type | Reported |
|----|-----------|------|----------|
| CR6 | #5 | bug | 2026-07-26 |
| CR7 | #2 | bug | 2026-07-26 |
| CR8 | #4 | feature | 2026-07-26 |
| CR9 | #1 | feature | 2026-07-26 |
| CR10 | #3 | feature | 2026-07-26 |

---

# Playtest findings — 2026-07-26 (prod, 9 turns)

Full evaluation in `docs/playtest-2026-07-26.md`.

## CR11 — [FIXED] Narrative→state bridge: chat actions never change mechanical state
**Severity:** CRITICAL (top priority) · relates to CR6, CR3

Across 9 prod turns, every `/chat` returned `state_updates: {}`. Buying, earning rewards,
completing tasks, combat, and hacking were all pure narration — coins stayed 100, inventory
unchanged, no quests/combat/minigame. The model emits only a `[Narration]` block and never
the `[StateUpdates]`/`[Events]` sections the parser expects, so the working sim (economy,
inventory, quests, combat, minigames) is unreachable from natural play.
**Fix:** enforce structured output — `narrative_prompt.j2` must REQUIRE a `[StateUpdates]`
JSON block every turn (explicit schema + few-shot + "emit `[StateUpdates] {}` if nothing
changed"); validate and retry once when it's missing. Largely resolves CR6 (perceived
inaccuracy = state desync) and CR3-in-practice (minigame_trigger never fires).
**Acceptance:** representative actions (buy/earn/take/attack/hack) produce corresponding
`state_updates` that the server applies (coins/inventory/quests/combat/minigame change).

## CR12 — [FIXED] `[Narration]` tag leaks into streamed narration
**Severity:** Low. The streaming path doesn't strip the `[Narration]` header (the
non-streaming parse does). Players can see the raw tag. Fix in the SSE chunk handling
(`engine`).

## CR13 — [RESOLVED — not a bug] SSE splits multibyte UTF-8 → mojibake
**Severity:** Low. The mojibake seen during the playtest was a **harness artifact** (the
Python playtest script decoded each SSE line independently). The frontend already decodes
the stream correctly with `TextDecoder('utf-8')` + `decode(value, { stream: true })`, which
handles multibyte characters split across chunks. No app change needed.

## Notes on existing items (from playtest)
- **CR6** — continuity was actually good (turn-8 recall of a turn-1 task); the felt
  "inaccuracy" is **state desync** → folds into CR11.
- **CR7** — NOT reproduced (5 clean locations; exploration is narrative-only). Needs a
  targeted repro after CR11 lands (watch for `location_name` updates creating near-dupes).
- **CR8** — confirmed: narration is rich but rarely leads; prompt-tunable.
