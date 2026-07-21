# Development Roadmap: Shangri-la: Age of Steam

## Phase 1: Infrastructure & Foundation (Completed)
- [x] Project Repository & Workspace Setup
- [x] Environment Configuration (Python 3.13, FastAPI, SQLModel, Vite, React 19)
- [x] Database Schema Implementation (`Location`, `NPC`, `WorldState`, `PlayerAction`)
- [x] Database Seeding & Initialization System (`database_init.py` with 3 core locations and NPCs)
- [x] CORS Middleware & FastAPI API endpoints (`/health`, `/state`, `/chat`, `/reset`)
- [x] vLLM Client Integration with Fallback & Offline Resilience (`client.py`)

## Phase 2: Narrative Engine & Core Logic (Completed)
- [x] Prompt Engineering & Templates (`narrative_prompt.j2`)
- [x] vLLM Inference Integration with flexible OpenAI/vLLM completion parsing
- [x] State Management & Persistence (`StateRepository`, `saos.db`)
- [x] Player Mood & Exploration Mode integration
- [x] Output Parsing (`[Narration]`, `[StateUpdates]`, `[Events]`)

## Phase 3: Frontend & User Experience (Completed)
- [x] React 19 / Vite / Tailwind CSS Steampunk Industrial UI
- [x] Interactive Terminal Narrative Feed with real-time state feedback
- [x] Active NPCs Panel with Disposition Meters & Persistent Memories Drawer
- [x] Environment Overview & Fast Travel Location Switcher
- [x] Action Bar with Player Mood selector and Exploration Mode toggle

## Phase 4: Next Major Milestones (Future Roadmap)
- [x] **Multi-Agent NPC Orchestration:** Enable real-time inter-NPC conversations in the same location.
- [x] **Dynamic Inventory & Quest Tracking:** Add item schemas, equipment management, and steam-tech crafting.
- [x] **Automata Companions System:** Create models and state logic for robotic pets that can act in combat and exploration.
- [x] **VLLM Streaming Output (Server-Sent Events / WebSockets):** Token-by-token narrative streaming for ultra-low latency presentation.
- [x] **Sabotage & Espionage Mini-games Engine:** Interactive CLI-like puzzles in the UI for hacking and deciphering.
- [x] **Dynamic Economy Engine:** State-driven fluctuating prices for resources.
- [x] **Complex Relationship & Faction System:** Deepen NPC disposition formulas with faction standing (e.g., Iron Syndicate vs Alchemists Guild).
- [x] **Audio Ambience & Sound Effects:** Add atmospheric steam/machinery audio clips and background music.
- [x] **Character Creation UI Wizard:** Interactive React component shown before gameplay to set up a player's class, stats, and backstory.
- [x] **Stats & Backstory Panel:** Persistent React sidebar/panel displaying the current character's statistics and history.

