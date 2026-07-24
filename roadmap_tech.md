# 🔧 Tech Roadmap — Shangri-La: Age of Steam

> **Lane: `T_phases`** — Testing, CI/CD, code quality, developer experience, and exciting technical upgrades.

---

## T_phase 1 — Frontend Testing Foundation

**Goal:** Eliminate the zero-test-coverage gap on the frontend. Establish a component testing pipeline so UI regressions are caught before merge.

- [ ] **Install Vitest + React Testing Library**: Add `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, and `jsdom` to `frontend/devDependencies`. Configure `vitest.config.ts` with `jsdom` environment and path aliases matching `tsconfig.app.json`. Add an `npm test` script to `package.json`.
- [ ] **Core Component Unit Tests**: Write unit tests for the 5 most critical components — `ChatInterface.tsx` (message rendering, action submission), `MarketUI.tsx` (buy/sell flow, price display), `CombatUI.tsx` (turn indicator, HP display), `CharacterCreation.tsx` (stat allocation validation), `SessionLobby.tsx` (session creation/join flow). Each test file should cover at minimum: renders without crash, handles empty state, responds to user interaction.
- [ ] **API Client Tests**: Write tests for `api.ts` using `msw` (Mock Service Worker) to mock backend responses. Cover the happy path and error states for `/chat`, `/state`, `/market/*`, and `/auth/*` endpoints.

---

## T_phase 2 — CI Pipeline Hardening

**Goal:** Make the CI pipeline a true quality gate — nothing merges unless backend tests, frontend tests, type checks, and linting all pass.

- [ ] **Frontend CI Job**: Add a new job to `.github/workflows/backend-ci.yml` (or create `ci.yml`) that runs `npm ci`, `npx tsc --noEmit` (type checking), `npm run lint` (oxlint), and `npm test` on every push/PR to `main`.
- [ ] **Python Linting in CI**: Add `ruff` to `pyproject.toml` dev dependencies. Configure `ruff.toml` with `select = ["E", "F", "I", "W"]` and `line-length = 120`. Add a `ruff check backend/` step to the CI workflow before pytest runs.
- [ ] **CI Status Badges**: Add build status badges to `README.md` for both backend and frontend CI workflows so contributors can see pipeline health at a glance.

---

## T_phase 3 — Backend Architecture Refactor

**Goal:** Break the monolithic `main.py` (1,300+ lines) into domain-scoped FastAPI routers for maintainability, testability, and onboarding speed.

- [ ] **Router Extraction**: Split `backend/main.py` into modular routers: `backend/routers/auth.py` (registration, login, session management), `backend/routers/gameplay.py` (chat, state, fast-travel, combat), `backend/routers/economy.py` (market, empire, properties, workers), `backend/routers/admin.py` (user management, prompt inspector, roadmap compiler), `backend/routers/workshop.py` (mod upload, browse, install). Register all routers in a slim `main.py` that only handles app lifecycle, middleware, and startup events.
- [ ] **Background Task Module**: Extract `world_simulation_loop`, `simulate_global_market`, and `simulate_faction_wars` into `backend/simulation.py`. Import and launch them from `main.py`'s `@app.on_event("startup")`.
- [ ] **Database Migration with Alembic**: Install Alembic, initialize with `alembic init`, configure it against `database.py`'s engine. Replace the ad-hoc `ALTER TABLE` try/catch blocks with proper migration scripts. Create an initial migration from the current schema as baseline.

---

## T_phase 4 — Frontend Architecture Refactor

**Goal:** Decompose the 875-line `ChatInterface.tsx` monolith and introduce proper state management so the frontend is maintainable and extensible.

- [ ] **State Management with Zustand**: Install `zustand`. Extract game state (character, inventory, quests, combat, market prices, world events) from `ChatInterface.tsx` into a `useGameStore` Zustand store in `frontend/src/stores/gameStore.ts`. Components subscribe to slices of state they need instead of prop-drilling through the chat interface.
- [ ] **ChatInterface Decomposition**: Split `ChatInterface.tsx` into focused modules: `NarrativeStream.tsx` (SSE parsing + message display), `ActionBar.tsx` (input + mood selector + mode toggle), `StateUpdateHandler.ts` (JSON state patch application), `WebSocketSync.ts` (market + event websocket management). The parent `ChatInterface.tsx` becomes a thin layout wrapper.
- [ ] **API Caching with TanStack Query**: Install `@tanstack/react-query`. Wrap API calls (`/state`, `/market/prices`, `/codex/*`) in `useQuery` hooks with stale-while-revalidate caching. This eliminates redundant fetches and provides loading/error states out of the box.

---

## T_phase 5 — E2E Testing & Quality Assurance

**Goal:** Add end-to-end testing that validates critical user journeys across the full stack — from browser to database and back.

- [ ] **Playwright E2E Setup**: Install `@playwright/test`. Configure `playwright.config.ts` to spin up both backend (pytest fixtures or Docker) and frontend dev server. Write E2E tests for: character creation flow, sending a chat action and receiving narrative response, buying/selling on the market, saving and loading game state.
- [ ] **E2E in CI**: Add a Playwright job to the CI workflow that runs against a test database with seeded data. Use `docker-compose` to spin up the full stack in CI. Upload test failure screenshots and traces as GitHub Actions artifacts.
- [ ] **Visual Regression Testing**: Add `@playwright/test` screenshot comparison for the 3 most visually complex pages (ChatInterface, MarketUI, CharacterCreation). Flag visual diffs in PRs.

---

## T_phase 6 — Interactive World Map (WebGL/Canvas)

**Goal:** Replace the static location dropdown with a visually stunning interactive steampunk map — the most exciting visual upgrade to the game.

- [ ] **Canvas 2D World Map Component**: Build a `WorldMap.tsx` component using **Pixi.js** or HTML5 Canvas. Render the 5+ locations as illustrated steampunk nodes on a parchment-textured map with brass-pipe connection lines. Clicking a node triggers fast-travel. Animate steam particles flowing along the pipes.
- [ ] **Faction Territory Overlay**: Color-code map regions by controlling faction. When `simulate_faction_wars` annexes a location, animate the territory color shift in real-time via WebSocket events. Display faction emblems on controlled territories.
- [ ] **Airship Travel Visualization**: When a player uses airship travel, animate their vessel moving along a dotted path between origin and destination nodes. Show altitude changes, weather effects (clouds, lightning), and fuel consumption as the journey progresses.

---

## T_phase 7 — PWA, Performance & Developer Experience

**Goal:** Make the game installable, performant, and a joy to develop on.

- [ ] **PWA with Offline Codex**: Install `vite-plugin-pwa`. Configure a Service Worker that caches static assets, the Codex encyclopedia data, and the last-loaded game state. Add a web app manifest with steampunk-themed icons. Players can install the game as a desktop/mobile app and browse the Codex offline.
- [ ] **Virtual List Rendering**: Replace the flat message list in `ChatInterface` with `react-virtuoso` or `@tanstack/react-virtual`. Only render visible messages in the DOM — critical for sessions with 500+ narrative entries.
- [ ] **Environment Templates & Onboarding**: Create `.env.example` files in both root and `frontend/` with all required variables documented. Add a `scripts/setup.sh` (or `setup.ps1`) that copies `.env.example` to `.env`, installs Python and Node dependencies, seeds the database, and prints a "ready to develop" message.
- [ ] **Hot Module Replacement Stability**: Audit `vite.config.ts` for HMR edge cases with WebSocket connections. Ensure the WebSocket reconnects cleanly after HMR reloads without spawning duplicate connections or losing game state.
