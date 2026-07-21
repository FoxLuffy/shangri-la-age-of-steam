# Shangri-La: Age of Steam - Roadmap V2.0 (The Empire & Warfare Update)

## Phase 1: Narrative-Driven Tactical Combat ⚔️
*Move beyond simple dice rolls by blending descriptive prose with hard tactical mechanics.*
- [x] **Dynamic Entity Stats:** Introduce HP, Armor, and Steam/Energy (mana) to the player and NPCs.
- [x] **Narrative Attack Parsing:** The LLM interprets freeform combat inputs (e.g., *"I sharpened my mind and aimed for his wings"*) and translates them into hard mechanics (e.g., calculates Critical Hit against 'Wings', reduces Enemy HP, expends 10 Steam).
- [x] **Status Effects & Overheating:** Introduce elemental and mechanical status effects (e.g., *Bleeding, Stunned, Overheated, Rusted*). If the player spams steam-abilities, they overheat and take damage.
- [x] **Combat UI State:** A distinct UI mode during combat that displays enemy health bars, targeted limbs, and the player's current Steam/Heat gauges.

## Phase 1.5: UX & Immersion Overhaul 🎨
*Smooth out interactions and add quality of life improvements.*
- [x] **Interactive Event Triggers:** Narrative popups (combat, lockpicking, etc.) are triggered by UI buttons in the dialogue bubble rather than automatically overlaying the screen.
- [x] **Tutorial Settings & Overlays:** Add a settings menu where tutorials for new screens can be toggled. Enabled by default (can be toggled during Character Creation). Every new screen or major change must include a tutorial overlay.
- [x] **Dynamic Gear Generation:** At character creation, add a prompt field to describe gear. System generates balanced starting items based on the class. (NO MAGICAL ITEM SPAWNS)

## Phase 2: Industrialist Empire & City Management 🏭
*Transition from a wandering adventurer to a baron of industry.*
- [x] **Real Estate Engine:** Properties (factories, shops) can be bought and managed.
- [x] **NPC Employment:** Hire NPCs as guards, managers, or laborers. Pay salaries.
- [x] **Passive Resource Generation:** Background simulation tracks factory outputs and generates wealth over time.
- [x] **Empire UI Panel:** Dedicated React dashboard to view holdings, worker morale, and net income.

## Phase 3: The Asynchronous Shared World 🌐
*A living, breathing universe shaped by the community.*
- [ ] **Global Market Sync:** The `ResourceMarket` connects to a global cloud database. If thousands of players buy Brass, the price skyrockets for everyone worldwide.
- [ ] **Faction Wars & Global Pledged Standing:** Player actions contribute to a global ledger. If players overwhelmingly support the Iron Syndicate, the Syndicate may permanently take over locations like the Undercity Slums.
- [ ] **Ghost Echoes:** Players can stumble upon the "echoes" of other players' actions in the world (e.g., arriving at a tavern to hear the bartender complain about a player who started a brawl there an hour ago).

## Phase 4: Community Modding Ecosystem 🛠️
*Give the players the keys to the steamworks.*
- [ ] **JSON Module Support:** A system allowing players to upload custom JSON files defining new Locations, NPCs, Items, and Factions.
- [ ] **Steam Workshop / Mod Browser:** An in-game hub to download and inject popular community modules directly into a local save state.
- [ ] **Custom AI System Prompts:** Advanced users can tweak the narrative prompt parameters of their custom NPCs to create entirely new genres within the engine.
