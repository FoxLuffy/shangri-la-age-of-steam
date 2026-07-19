# Development Roadmap: Shangri-la: Age of Steam

An immersive, text-driven RPG powered by FastAPI, SQLModel, React, and vLLM inference backends.

---

## 🛠️ Current Project Status & Completed Fixes

All core infrastructure, database schemas, API backends, and frontend components have been fixed, verified, and are fully runnable.

### Key Actions & System Fixes Implemented:
1. **Dynamic Database Persistence:** Fixed `backend/database.py` to check for docker volume mount `/data` or `DATABASE_DIR` env variables, preventing data loss on restarts.
2. **CORS Middleware Integration:** Added `CORSMiddleware` configuration to `backend/main.py` to allow cross-origin requests from frontend hosts/ports.
3. **Template Loading Fix:** Corrected `backend/prompt_utils.py` to load Jinja2 templates using file-relative paths, avoiding `FileNotFoundError` across different run directories.
4. **Redesigned Cyberpunk/Steampunk Dashboard UI:** Complete overhaul of `frontend/src/components/ChatInterface.tsx` to build a responsive two-column grid. Added NPC trait badges, dynamic disposition gauges, character mood options, and exploration settings.
5. **Tailwind CSS Generation:** Corrected `frontend/src/index.css` by importing Tailwind directives and configured `frontend/tailwind.config.js` to scan source files.
6. **Dynamic API base URL:** Updated `frontend/src/api.ts` to automatically detect window locations, streamlining remote deployments without hardcoded configurations.
7. **Clean Docker Configurations:** Fixed both `Dockerfile.backend` and `Dockerfile.frontend` path syntax and environment format bugs. Created a custom `nginx.conf` supporting frontend single-page routing on port 5173.
8. **Docker Compose Support:** Updated `docker-compose.yml` to specify local `build:` blocks for both frontend and backend.

---

## 📈 Development Phases

### 🟩 Phase 1: Infrastructure & Foundation (Complete)
- [x] Project Repository Setup
- [x] Environment Configuration (Python, FastAPI, SQLModel)
- [x] Database Schema Implementation
- [x] Dynamic SQLite Persistence & Mount Checks
- [x] CLI testing scripts & verification

### 🟩 Phase 2: Narrative Engine & Core Logic (Complete)
- [x] Steampunk Narrative Jinja2 Templates
- [x] State-Aware Prompt Engineering (`prompt_utils.py`)
- [x] VLLM Inference Client Setup & Mock Tests
- [x] Core Narrative Flow Engine (`engine.py`)
- [x] Automated Unit Testing suite (7/7 passing)

### 🟩 Phase 3: Frontend & Single-Page User Experience (Complete)
- [x] React 19 + TypeScript + Vite Scaffold Setup
- [x] Steampunk Glassmorphic Dashboard Design
- [x] Responsive layout with Location details and NPC status indicators
- [x] Live connection updates and dynamic mood input modifiers
- [x] Production SPA Nginx deployment configuration on port 5173

### 🟦 Phase 4: Advanced Gameplay Features (Planned)
- [ ] **Multi-Agent NPC Interactions:** Allow NPCs to interact with each other in the room, creating emergent dialog.
- [ ] **NPC Relationship & Memory Graph:** Expand NPC database memory schema to record positive/negative interactions with semantic weights.
- [ ] **Item & Inventory State:** Add items to world state schemas, allowing players to obtain items and use them to unlock actions.
- [ ] **Dynamic Environment Triggers:** Trigger global events based on cumulative player actions (e.g., boiler explosion, security lockdown).

### 🟦 Phase 5: Production scale & Deployment (Planned)
- [ ] **TrueNAS SCALE integration testing:** Verify Docker-Compose orchestration via TrueNAS Custom Apps.
- [ ] **HuggingFace/vLLM backend setup:** Add guides for launching local model servers (e.g., Llama-3-8B-Instruct or Mistral-7B-Instruct).
- [ ] **User Authentication & Cloud Sync:** Add multi-user account logins to persist distinct player campaign instances.
