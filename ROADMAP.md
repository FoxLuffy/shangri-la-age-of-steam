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
- C3 [COMPLETE] Crafting Depth & Recipe Discovery
      - C3.1 [COMPLETE] Recipe discovery: KnownRecipe table (unique char+recipe), router
        backend/routers/crafting.py — GET /crafting/known, POST /crafting/discover
        (generic grant for dialogue/exploration/purchase paths), POST /crafting/experiment
        (materials → RNG discovery). /craft gated 403 until discovered; zero starter recipes.
        Alembic migration d5b2c9f1a3e8. 7 tests in test_crafting_discovery.py.
      - C3.2 [COMPLETE] Specialization trees: Recipe.branch + Recipe.tier;
        CraftingProficiency table (per char+branch, xp → level 0–10, cap). GET
        /crafting/proficiency. /craft — branched recipes: tier-gate (400 if underleveled),
        proficiency-scaled success roll (fail wastes materials), +1 XP on success;
        branchless recipes stay deterministic. Migration e7c4a2b9f1d0. 6 tests in
        test_crafting_specialization.py.
      - C3.3 [COMPLETE] CraftingPanel.tsx — modal (Workbench) with proficiency bars,
        known-recipe browser (requirements have/need + success %), Craft, and a
        click-select experimentation grid. Backend reads enriched: /crafting/known
        (branch/tier/result_name/requirements) + new /crafting/materials. api.ts
        helpers + craftSuccessPct. Wired via StatsPanel/App. 5 frontend + 2 backend tests.
- C4 [COMPLETE] Multiplayer social: trading, guilds, bulletin board
- C5 [COMPLETE] Dynamic weather & day/night + seasonal events
- C6 [COMPLETE] Bounty board & procedural missions
- C7 [COMPLETE] Artifact collection & journal
- C8 [COMPLETE] Expanded Modding Ecosystem
      - C8.1 [COMPLETE] Mod SDK docs: docs/modding_guide.md (upload, {factions,locations,
        npcs,items} schema, per-field tables, upsert rules, ItemCategory enum, annotated
        example, validation notes, Planned section) + runnable docs/mods/example_mod.json
        guarded by test_modding_example.py (uploads → asserts entities created).
      - C8.2 [COMPLETE] Mod validation in /modding/upload: backend/mod_validation.py
        (pydantic strict schemas per entity; required/type/unknown-field + ItemCategory
        checks; in-file id/name uniqueness; referential existence in DB or same file).
        Collect-all, atomic reject → 400 with detail=[messages]; valid mods still apply.
        Guide validation section updated. 12 tests in test_mod_validation.py.
      - C8.3 [COMPLETE] Mod rating & curation: ModRating model (unique mod+user, upsert)
        + migration f1a8d3c6b2e9. POST /workshop/mods/{id}/rate (1–5, 400 otherwise),
        GET /workshop/mods enriched (avg_rating/rating_count/featured: avg≥4.5&≥1 or flag),
        GET /workshop/mods/{id}/ratings. WorkshopBrowser: star widget, sort (rating/downloads),
        featured carousel; userId wired from App. 6 backend + 4 frontend tests.
      - C8.4 [COMPLETE] Mod chains & dependencies: registry `dependencies` field;
        resolve_install_order (topological, missing + cycle detection); install auto-installs
        deps first with per-mod try/except → {installed, warnings}; GET
        /workshop/mods/{id}/dependencies preview. Sample mod files repaired; apply_mod_data
        helper. WorkshopBrowser shows "Requires". 7 backend + 1 frontend tests.

## D. Technical Quality (built — checkboxes were stale)
- D1 [COMPLETE] Frontend testing: vitest + RTL + msw, 58 tests
- D2 [COMPLETE] CI hardening: ruff + pytest + oxlint + tsc + vitest + Playwright, badge
- D3 [COMPLETE] Backend refactor: routers/, simulation.py, Alembic migrations
- D4 [COMPLETE] Frontend refactor: zustand store, ChatInterface decomposition, react-query
- D5 [COMPLETE] E2E & QA: Playwright visual regression for the 3 named screens
      (CharacterCreation, ChatInterface, MarketUI) via toHaveScreenshot, linux+win32
      baselines, CI runs + uploads diff report if:failure(). Hardened: .gitattributes marks
      baselines binary (autocrlf-safe); frontend/e2e/README.md documents the suite + per-
      platform baseline regeneration. (Further screens need CI-generated linux baselines.)
- D6 [COMPLETE] Interactive World Map: faction territory overlay (nodes colored by
      faction_id + HTML legend) and airship travel animation (dashed route, oriented
      airship glyph, progress/altitude readout). Pure helpers in utils/worldMapUtils.ts
      (factionColor/easeInOutQuad/travelPoint/altitudeForProgress/humanizeFactionId).
      Location type gains faction_id. 9 util + 3 component tests. (Real-time war recolor,
      emblems, weather FX intentionally deferred.)
- D7 [COMPLETE] PWA/perf/DX: vite-plugin-pwa, react-virtuoso, .env.example, scripts/

## E. Save State Management (NEW)
> Model: ONE save slot per character (single SaveState row, unique character_id).
> Manual save and autosave both overwrite that one slot — no multi-slot per character.
- E1 [COMPLETE] Character sessions: GET /sessions/{user_id} enriched with per-character
      save metadata — has_save, last_saved (SaveState.created_at), location_name (current
      location resolved). Shown on CharacterCreation session cards (location + last-saved,
      or "No save yet"). repository.get_sessions; 2 backend + 2 frontend tests.
- E2 [COMPLETE] Manual save/load, single slot per character: POST /saves (create or
      overwrite), GET /saves/{character_id}, GET /saves/{character_id}/load,
      DELETE /saves/{character_id}. Snapshot = character + world + quest + inventory.
      Router backend/routers/saves.py, SaveState model (unique character_id),
      Alembic migration c3a1f0e2d4b7. 8 tests in test_save_state.py.
- E3 [COMPLETE] Autosave: frontend-driven, one living save (overwrites the single slot
      via createSave). Periodic every 5 player actions + pre-travel checkpoint. No
      pre-combat (combat is emergent). Module frontend/src/utils/autosave.ts wired into
      ChatInterface (submitAction + handleLocationSwitch); best-effort, never blocks
      gameplay. 5 tests in autosave.test.ts.
- E4 [COMPLETE] Export/import save (JSON) with schema validation. GET
      /saves/{character_id}/export → versioned SaveExport (schema_version=1);
      POST /saves/{character_id}/import validates via pydantic (422 malformed, 400 bad
      version, 404 unknown char) then fills the slot (user Loads after). Export/Import
      buttons in SaveManager (Blob download; file → parse → confirm → import). 6 backend
      + 3 frontend tests.
- E5 [COMPLETE] Save UI: SaveManager.tsx rendered inside the in-game SettingsMenu —
      Save (create/overwrite), Load, Delete, with window.confirm on Load + Delete.
      api.ts helpers (createSave/getSave/loadSave/deleteSave); Load reloads the app to
      re-fetch restored state. 7 tests in SaveManager.test.tsx. (Rename/export deferred
      to E4; placed in SettingsMenu not SessionLobby since resume is automatic and the
      lobby has no active character.)

## F. Housekeeping
- F1 [COMPLETE] Fixed pytest-from-subdir: backend/tests/conftest.py prepends the repo
      root to sys.path, so `pytest` works from the repo root OR backend/ (was
      ModuleNotFoundError: backend). README gains a "Running the tests" section.
- F2 [COMPLETE] Removed all datetime.utcnow() (deprecated) from backend source (19 sites,
      8 files). New backend/timeutils.py (utcnow/utcnow_naive/utc_iso) preserves exact
      timestamp formats ("...Z"). 3 tests in test_timeutils.py; suite 114 green, ruff clean.
- F3 [COMPLETE] Resolved the character<->guild circular FK DROP warning: Guild.leader_id
      uses ForeignKey(use_alter=True) so DDL ordering works. 2 tests in test_fk_cycle.py
      (no warning + relationship intact); suite 116 green, warning count 0.
