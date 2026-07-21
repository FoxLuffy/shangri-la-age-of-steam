# Feature Roadmap: Shangri-la: Age of Steam

## Phase 1: Foundation (Completed)
- [x] Project Repository & Workspace Setup
- [x] Environment Configuration (Python 3.13, FastAPI, SQLModel, Vite, React 19)
- [x] Database Schema Implementation (Location, NPC, WorldState, PlayerAction)
- [x] Database Seeding & Initialization System
- [x] CORS Middleware & FastAPI API endpoints
- [x] vLLM Client Integration
- [x] Prompt Engineering & Templates
- [x] State Management & Persistence
- [x] React Frontend UI

## Phase 2: Narrative & Interaction (Completed)
- [x] Prompt Engineering & Templates
- [x] vLLM Inference Integration
- [x] State Management & Persistence
- [x] Player Mood & Exploration Mode integration
- [x] Output Parsing

## Phase 3: User Experience (Completed)
- [x] React 19 / Vite / Tailwind CSS Steampunk UI
- [x] Interactive Terminal Narrative Feed
- [x] Active NPCs Panel with Disposition Meters
- [x] Environment Overview & Fast Travel

## Phase 4: Advanced Mechanics (Completed)
- [x] **Character Creation & Presets**: Allow the player to choose from presets (e.g., Aristocrat, Scrapper, Alchemist) or create a custom character before starting.
- [x] **Multi-Agent NPC Orchestration**: Autonomous NPC interactions.
- [x] **Dynamic Inventory & Quest Tracking**: Persistent items, crafting, and quest states.
- [x] **Real-Time Streaming**: SSE-based chunk-by-chunk narrative.

## Phase 5: Content Depth & Systems (Next)
- [x] **Complex Relationship & Faction System**: Faction standing (Iron Syndicate vs. Alchemists Guild).
- [x] **Dynamic World Events**: Procedural world events (steam leaks, riots, industrial accidents).
- [x] **Procedural NPC Generation**: Randomized unique NPCs based on local regional "flavors."
- [x] **Faction-based Crafting**: Certain items only craftable in specific faction zones.

## Phase 6: Deep Gameplay Mechanics (New)
- [x] **Automata Companions**: Build, upgrade, and customize robotic steam-driven companions (clockwork owls, brass hounds) to assist in quests.
- [x] **Dynamic Economy Engine**: Simulated trade economy where coal, brass, and aether prices fluctuate dynamically based on world events and player actions.
- [x] **Steam-Tech Augmentations**: Player character cybernetics (steampunk style). Replace limbs with pneumatic prosthetics for unique abilities.
- [x] **Sabotage & Espionage Mini-games**: Text-based puzzle interfaces for hacking pneumatic tube networks, picking gear-locks, and deciphering alchemical recipes.
- [x] **Airship Mobile Base**: Acquire, customize, and pilot a steam-dirigible to access high-altitude zones and airborne faction battles.

## Phase 7: Frontend Systems & UI (Next)
- [x] **Character Creation Flow**: An introductory UI wizard shown at the beginning of the game to select a preset or customize character class, backstory, and initial stats.
- [x] **Stats & Backstory Panel**: A dedicated UI panel on the frontend displaying the player's current class, background story, and dynamic stats (`strength`, `intellect`, `charm`).

## Phase 8: Multimedia & Atmosphere (Future)
- [x] **Audio Ambience & Sound Effects**: Spatial audio and machinery-driven soundscapes.
- [x] **Dynamic Music**: Procedural music that reacts to player mood and location danger.
- [x] **Visual Narrative Effects**: Dynamic text styling (shake, color shifts) based on content sentiment.

## Phase 9: Social & Persistence (Future)
- [x] **Persistent World History**: A searchable "ledger" of all major narrative decisions.
- [x] **Multiplayer Sync (Experimental)**: Shared world state for group exploration.
- [x] **Save State Serialization**: Full state exports/imports for cross-device play.
