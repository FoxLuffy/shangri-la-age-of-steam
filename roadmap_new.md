# 🚀 New Features Roadmap — Shangri-La: Age of Steam

> **Lane: `N_phases`** — Net-new gameplay features, systems, and player-facing capabilities.

---

## N_phase 1 — Airship Navigation & Aerial Exploration

**Goal:** Activate the existing `Airship` schema into a full gameplay system — players acquire, customize, and pilot airships between locations with real flight mechanics.

- [ ] **Airship Hangar UI**: Build an `AirshipPanel.tsx` React component accessible from the main UI. Display the player's airship stats (hull integrity, fuel level, altitude ceiling, installed modules) with steampunk gauge visualizations (circular dials with brass bezels). Include buttons for refueling, repairing, and managing modules.
- [ ] **Flight Navigation System**: Implement a `/airships/navigate` endpoint that calculates travel time between locations based on distance, wind resistance (random per-tick), and engine module quality. During flight, stream narrative descriptions of the journey (cloud formations, other airships, weather hazards) via SSE. Fuel depletes proportionally to distance and altitude.
- [ ] **Aerial Encounters**: During airship travel, trigger random encounters (sky pirates, aether storms, floating trade barges, distress signals). Each encounter presents a choice: engage, evade, or investigate. Outcomes affect hull integrity, fuel, cargo, and reputation.

---

## N_phase 2 — Body Augmentation & Cybernetics

**Goal:** Activate the existing `Augmentation` schema into a character progression system — players install steam-powered body modifications that grant abilities at a cost.

- [ ] **Augmentation Clinic UI**: Build an `AugmentationPanel.tsx` component. Display a stylized human silhouette with socket slots (left arm, right arm, eyes, torso, legs). Each slot can hold one augmentation. Show installed augmentations with stat bonuses and side effects.
- [ ] **Augmentation Catalog & Installation**: Create a `/augmentations/catalog` endpoint listing available augmentations (Pneumatic Arm: +3 Strength, Steam-Eye Lens: +2 Intellect but -1 Charm, Clockwork Legs: +3 Speed). Installation requires brass coins, specific crafting materials, and visiting a location with a clinic NPC. Add a `body_slots` field to the Character model.
- [ ] **Augmentation Side Effects & Narrative Integration**: Each augmentation carries a `strain` value. Total strain above a threshold triggers narrative consequences — NPCs react with fear or fascination, certain factions refuse to deal with "metal-bloods", and the character's backstory panel updates to reflect their transformation. High-strain characters unlock unique dialogue options.

---

## N_phase 3 — Crafting Depth & Recipe Discovery

**Goal:** Expand the basic crafting system into a discovery-driven progression loop where players experiment, research, and specialize.

- [ ] **Recipe Discovery System**: Recipes are not known by default. Players discover them through: NPC dialogue (Alchemists reveal formulas at high disposition), exploration (finding blueprints in new locations), experimentation (combining materials at a workbench with a chance of discovery), or purchasing from the Workshop mod market. Store discovered recipes per-character in a `known_recipes` table.
- [ ] **Crafting Specialization Trees**: Define 3 crafting branches — **Metallurgy** (weapons, armor, structural components), **Alchemy** (potions, transmutations, volatile compounds), **Clockwork** (automata modules, precision instruments, traps). Each branch has a proficiency level (0–10) that unlocks higher-tier recipes and improves success rates.
- [ ] **Crafting Workbench UI**: Build a `CraftingPanel.tsx` component with a drag-and-drop material grid, recipe browser filtered by known recipes, and a crafting progress bar. Show success probability based on proficiency, materials quality, and available facility tier.

---

## N_phase 4 — Multiplayer Social Systems

**Goal:** Deepen the multiplayer experience beyond shared narrative space — add direct player-to-player interaction mechanics.

- [ ] **Player Trading System**: Implement `/trade/offer` and `/trade/accept` endpoints. Players in the same location can propose item/currency trades via a split-screen trade modal. Both parties must confirm before the transaction executes. Add a `TradeHistory` ledger table for audit trails.
- [ ] **Guild Formation**: Allow players to form named guilds with a shared treasury, guild emblem, and member roster. Guilds can collectively own properties, pool resources for large crafting projects, and declare allegiance to a faction (boosting faction standing for all members). Implement `/guilds/create`, `/guilds/invite`, `/guilds/treasury` endpoints and a `GuildPanel.tsx` component.
- [ ] **Player Messaging & Bulletin Board**: Add a `/messages/send` endpoint for async player-to-player messages delivered on next login. Build a `BulletinBoard.tsx` component at each location where players can post public notices (trade offers, warnings, recruitment, role-play flavor text). Messages persist for 7 in-game days.

---

## N_phase 5 — Dynamic Weather & Time System

**Goal:** Make the world feel temporally alive — a day/night cycle and weather system that affect gameplay, narrative, and visuals.

- [ ] **World Clock & Day/Night Cycle**: Add a `world_time` field to `WorldState` that advances with each simulation tick. Define 4 time periods (Dawn, Day, Dusk, Night). The narrative prompt receives the current period and adjusts descriptions — lamplighters igniting gas lamps at dusk, night markets opening, Syndicate patrols doubling after dark. The frontend UI shifts color temperature (warm amber → cool blue) based on time period.
- [ ] **Dynamic Weather Engine**: Each simulation tick rolls weather for each location: Clear, Overcast, Fog, Rain, Thunderstorm, Aether Storm. Weather affects: market prices (storms disrupt supply lines → price spikes), combat modifiers (fog reduces ranged accuracy, rain extinguishes fire), NPC behavior (NPCs seek shelter, smugglers prefer fog), and narrative descriptions.
- [ ] **Seasonal Events**: Define a 4-season calendar with annual events — The Brass Festival (crafting XP bonus), The Fog Season (increased random encounters), The Founder's Day (faction recruitment drives), The Long Dark (resource scarcity + exclusive quest availability).

---

## N_phase 6 — Bounty Board & Procedural Missions

**Goal:** Provide an infinite content loop — procedurally generated missions that reward exploration, combat, and faction engagement.

- [ ] **Bounty Board System**: Add a `BountyBoard` model and `/bounties/list` endpoint. Each location generates 3 active bounties per simulation cycle. Bounty types: Hunt (defeat a target NPC), Delivery (transport goods between locations), Investigation (gather clues from NPCs), Sabotage (use minigames to disrupt a rival faction's operation). Bounties expire after N ticks and reward brass coins, faction standing, and rare crafting materials.
- [ ] **Procedural Mission Generator**: Build `mission_generator.py` that assembles missions from template components: objective (kill/fetch/escort/investigate), target (procedurally named NPC or location), complication (time limit, rival bounty hunter, moral dilemma), and reward tier. The generator uses current world state (active faction wars, market prices, weather) to create contextually relevant missions.
- [ ] **Bounty Board UI**: Build a `BountyBoard.tsx` component styled as a cork board with pinned parchment notes. Each bounty shows its type icon, brief description, reward, expiration timer, and an "Accept" button. Active bounties appear in the quest tracker.

---

## N_phase 7 — Expanded Modding Ecosystem

**Goal:** Transform the basic workshop into a full modding platform that enables community-driven content creation.

- [ ] **Mod SDK Documentation**: Write a comprehensive modding guide (`docs/modding_guide.md`) covering the JSON mod schema, available entity types (locations, NPCs, factions, items, recipes, bounties), validation rules, and example mods. Include a template mod with inline comments.
- [ ] **Mod Validation & Sandboxing**: Add server-side mod validation in `/modding/upload` — schema validation (required fields, type checks, ID uniqueness), content safety checks (text length limits, prohibited terms), and dependency resolution (mods that reference base-game entities verify they exist). Return detailed validation errors to the uploader.
- [ ] **Mod Rating & Curation**: Add a `ModRating` model. Players can rate installed mods (1–5 stars) and leave short reviews. The `WorkshopBrowser.tsx` sorts by rating, download count, and recency. Featured mods (manually curated or auto-promoted at 4.5+ stars) appear in a highlighted carousel at the top of the browser.
- [ ] **Mod Chains & Dependencies**: Support mods that depend on other mods (e.g., a quest mod that requires a location mod). Define a `dependencies` field in the mod schema. The installer resolves and installs dependencies automatically, warning the player if a dependency is missing or incompatible.
