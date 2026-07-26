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

## CR2 — [OPEN] Bounty board crashes: `Unexpected token '<' … is not valid JSON`
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

## CR3 — [OPEN] "Start minigame" does nothing
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

## CR4 — [OPEN] NPCs missing from the Environment overview
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

## CR5 — [OPEN] Dynamic events dump raw/unclear data (immersion-breaking)
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
