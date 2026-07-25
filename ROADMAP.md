# 🗺 ROADMAP — Shangri-La: Age of Steam

Unified roadmap. Supersedes development_roadmap.md, ROADMAP_STORY.md,
roadmap_tech.md, roadmap_new.md. Each item has an ID targetable by `saosgo <ID>`.

Status legend: [COMPLETE] [PARTIAL] [BROKEN] [NOT STARTED]

> Test baseline: 54 backend (run from repo ROOT), 58 frontend. Run backend as
> `pytest` from repo root — `backend/` cwd breaks imports.

---

## A. Foundation & Core (Shipped)
- A1 [COMPLETE] Infra: FastAPI/SQLModel/Vite/React19, schema, seeding, CORS, vLLM client
- A2 [COMPLETE] Narrative engine: prompts, inference parsing, state persistence, moods
- A3 [COMPLETE] Frontend UX: steampunk UI, narrative feed, NPC panel, fast-travel, action bar
- A4 [COMPLETE] Systems: multi-agent NPCs, inventory/quests, automata, SSE streaming,
      minigames, dynamic economy, factions, audio, character creation, stats panel

## B. Story & World (Shipped)
- B1 [COMPLETE] Codex + faction dossiers + location lore cards
- B2 [COMPLETE] Faction dialect/greeting/tension dialogue
- B3 [COMPLETE] Automata sentience escalation + Forbidden Sentience questline
- B4 [COMPLETE] Espionage: MissionArc, Formula Heist, Double Agent
- B5 [COMPLETE] Living districts: condition metric, decay tiers, legacy monuments
- B6 [COMPLETE] Sensory: dynamic audio score, spatial soundscapes, steam intensity FX
- B7 [COMPLETE] Character origins + NPC relationship arcs + NPC-to-NPC web

## C. New Gameplay Features
- C1 [COMPLETE] Airship navigation & aerial encounters
- C2 [COMPLETE] Body augmentation & cybernetics
- C3 [NOT STARTED] Crafting Depth & Recipe Discovery
      - C3.1 Recipe discovery system (known_recipes table, 4 discovery paths)
      - C3.2 Crafting specialization trees (Metallurgy/Alchemy/Clockwork, 0–10 proficiency)
      - C3.3 CraftingPanel.tsx (drag-drop grid, recipe browser, success probability)
- C4 [COMPLETE] Multiplayer social: trading, guilds, bulletin board
- C5 [COMPLETE] Dynamic weather & day/night + seasonal events
- C6 [COMPLETE] Bounty board & procedural missions
- C7 [COMPLETE] Artifact collection & journal
- C8 [NOT STARTED] Expanded Modding Ecosystem
      - C8.1 Mod SDK docs (docs/modding_guide.md + template mod)
      - C8.2 Mod validation & sandboxing in /modding/upload
      - C8.3 Mod rating & curation (ModRating, sorted browser, featured carousel)
      - C8.4 Mod chains & dependencies (dependency resolution on install)

## D. Technical Quality (built — checkboxes were stale)
- D1 [COMPLETE] Frontend testing: vitest + RTL + msw, 58 tests
- D2 [COMPLETE] CI hardening: ruff + pytest + oxlint + tsc + vitest + Playwright, badge
- D3 [COMPLETE] Backend refactor: routers/, simulation.py, Alembic migrations
- D4 [COMPLETE] Frontend refactor: zustand store, ChatInterface decomposition, react-query
- D5 [PARTIAL] E2E & QA: Playwright configured + specs + CI job; expand visual-regression
- D6 [PARTIAL] Interactive World Map: WorldMap.tsx exists; verify/complete faction
      territory overlay + airship travel animation
- D7 [COMPLETE] PWA/perf/DX: vite-plugin-pwa, react-virtuoso, .env.example, scripts/

## E. Save State Management (NEW)
> Model: ONE save slot per character (single SaveState row, unique character_id).
> Manual save and autosave both overwrite that one slot — no multi-slot per character.
- E1 [PARTIAL] Character sessions: /sessions/{user_id} lists a user's characters —
      add per-character save metadata (last-saved timestamp, location preview)
- E2 [COMPLETE] Manual save/load, single slot per character: POST /saves (create or
      overwrite), GET /saves/{character_id}, GET /saves/{character_id}/load,
      DELETE /saves/{character_id}. Snapshot = character + world + quest + inventory.
      Router backend/routers/saves.py, SaveState model (unique character_id),
      Alembic migration c3a1f0e2d4b7. 8 tests in test_save_state.py.
- E3 [NOT STARTED] Autosave & checkpoints: periodic + pre-combat/pre-travel autosave
      that overwrites the character's single slot (reuses POST /saves)
- E4 [NOT STARTED] Export/import save (JSON download/upload) with schema validation
- E5 [COMPLETE] Save UI: SaveManager.tsx rendered inside the in-game SettingsMenu —
      Save (create/overwrite), Load, Delete, with window.confirm on Load + Delete.
      api.ts helpers (createSave/getSave/loadSave/deleteSave); Load reloads the app to
      re-fetch restored state. 7 tests in SaveManager.test.tsx. (Rename/export deferred
      to E4; placed in SettingsMenu not SessionLobby since resume is automatic and the
      lobby has no active character.)

## F. Housekeeping
- F1 [NOT STARTED] Fix pytest-from-subdir failure OR document root-only rule in README
- F2 [NOT STARTED] Address datetime.utcnow() deprecation warnings (repository.py, gameplay.py)
- F3 [NOT STARTED] Resolve SQLAlchemy character<->guild circular FK DROP warning (use_alter=True)
