# 📜 Story Roadmap — Shangri-La: Age of Steam

> **Lane: `S_phases`** — World-building, lore depth, narrative systems, and immersive storytelling.

---

## S_phase 1 — Codex & Static Lore Foundation

**Goal:** Create a browsable in-game encyclopedia that gives the world historical weight beyond what the LLM generates on the fly.

- [ ] **World Codex System**: Build a `codex/` data directory with structured Markdown or JSON entries for lore topics (History of Shangri-La, The Great Steam Awakening, The Aether Schism, etc.). Expose a `/codex` API endpoint and a React `CodexBrowser` component with category tabs (History, Factions, Technology, Geography).
- [ ] **Faction Dossiers**: Write rich backstory entries for the Iron Syndicate, Alchemists Guild, and Undercity Smugglers — origins, internal hierarchies, signature technologies, and rivalries. Each dossier should include a leader profile, 3 notable historical events, and a current-era agenda.
- [ ] **Location Lore Cards**: Extend each of the 5 seeded locations with a `lore_text` field containing 2–3 paragraphs of atmospheric history. Surface these in the UI as expandable cards when the player arrives at a location for the first time.

---

## S_phase 2 — Faction Identity & Linguistic Texture

**Goal:** Make each faction feel culturally distinct through language, rituals, and social norms — so players can *hear* who they're talking to.

- [ ] **Faction Dialect Prompts**: Create per-faction Jinja2 prompt fragments injected into `narrative_prompt.j2` when an NPC speaks. Iron Syndicate NPCs use clipped, technical jargon ("pressure tolerances", "yield ratios"). Alchemists speak in measured, academic prose with Latin-adjacent terminology. Undercity Smugglers use slang, contractions, and underworld cant.
- [ ] **Faction Greeting Rituals**: Define cultural interaction patterns — Syndicate engineers exchange tool salutes, Alchemists offer vial-clinks, Smugglers use coded hand signs. Embed these in NPC interaction prompts.
- [ ] **Cross-Faction Tension Dialogue**: When NPCs from rival factions occupy the same location, the overheard-dialogue system (`trigger_npc_interaction`) should inject faction-specific hostility, suspicion, or negotiation patterns based on faction relationship scores.

---

## S_phase 3 — Automata Sentience & Companion Arcs

**Goal:** Transform automata companions from passive inventory items into narrative actors with their own emergent storylines.

- [ ] **Automata Personality Seeds**: When an automata companion is acquired, generate a personality profile (curious, loyal, erratic, philosophical) via vLLM. Store this in the `AutomataCompanion` model as `personality_traits` and `core_directive`.
- [ ] **Sentience Escalation System**: Track an internal `sentience_score` (0–100) on each automata. Certain player actions (feeding it aether crystals, exposing it to the Observatory, talking to it repeatedly) increment the score. At thresholds (25, 50, 75, 100), trigger narrative events — the automata asks a question, disobeys an order, expresses fear of deactivation, or demands freedom.
- [ ] **The Forbidden Sentience Questline**: At `sentience_score >= 75`, unlock a branching quest: the player must choose to suppress the automata's awakening (keeping it loyal but hollow), help it achieve full sentience (risking Syndicate persecution), or sell the research to the Alchemists Guild. Each branch permanently alters faction standings and unlocks unique narrative endings.

---

## S_phase 4 — Corporate Espionage & Intrigue Arcs

**Goal:** Build structured multi-stage story arcs around industrial sabotage, formula theft, and political manipulation — connecting the existing minigame mechanics to narrative consequences.

- [ ] **Espionage Mission Framework**: Create a `MissionArc` model with stages (briefing → infiltration → extraction → fallout). Each stage has success/failure conditions, skill checks (Intellect for decryption, Speed for escape, Charm for bluffing guards), and narrative branching.
- [ ] **Formula Heist Arc**: A 4-stage quest where the Alchemists Guild hires the player to steal a proprietary alloy formula from an Iron Syndicate foundry. Stage 1: Social engineering an NPC contact. Stage 2: Hacking minigame to bypass security. Stage 3: Lockpicking minigame in the vault. Stage 4: Escape sequence with pursuit logic. Failure at any stage creates cascading consequences (bounty, faction hostility, NPC betrayal).
- [ ] **Double Agent System**: Allow players to accept missions from multiple factions simultaneously. Track a `cover_integrity` score — performing contradictory actions degrades it. If it drops to zero, the player is exposed and both factions become hostile. NPCs with high disposition may warn the player before exposure.

---

## S_phase 5 — Environmental Storytelling & Living Districts

**Goal:** Make the city itself a character — districts that visibly evolve based on player actions and global simulation state.

- [ ] **District Condition System**: Add a `condition` metric (0–100) to each location representing its physical state (0 = ruined, 100 = thriving). Player empire-building, faction wars, and world events shift conditions. The narrative prompt receives the condition score and adjusts descriptions accordingly — crumbling walls and flickering gas lamps vs. polished brass facades and bustling markets.
- [ ] **Environmental Decay/Progress Descriptions**: Write 3 tiers of environmental prose per location (decayed, neutral, prosperous) stored in `lore_text_tiers`. The narrative engine selects the appropriate tier based on current condition.
- [ ] **Player Legacy Monuments**: When a player's industrial influence in a district exceeds a threshold, permanently add a named landmark (statue, renamed street, commemorative plaque) to the location's description. These persist across all player sessions as shared world history.

---

## S_phase 6 — Sensory Narrative & Atmospheric Immersion

**Goal:** Engage all senses — audio, visual cues, and tactile language — to make the steampunk world feel physically present.

- [ ] **Dynamic Audio Score Engine**: Map narrative tags (combat, mystery, discovery, dread, celebration) to ambient audio tracks. When the LLM emits a `[mood:combat]` tag, the frontend crossfades to a tense percussion track. Extend `AudioManager.tsx` with a mood-to-track mapping system.
- [ ] **Spatial Soundscapes per Location**: Assign each location a layered ambient loop — The Grand Foundry gets hammering + hissing steam + distant shouting. The Aetherium Observatory gets wind + crystalline hum + quill scratching. Trigger these on location change.
- [ ] **Visual Steam Intensity**: Add a CSS particle effect layer to the `ChatInterface` that adjusts steam/fog density based on the current location's industrial rating. Foundry = dense amber fog. Observatory = faint blue wisps. Undercity = dark, oily haze.

---

## S_phase 7 — Character Origins & Relationship Depth

**Goal:** Give every player character a rich past and let NPC relationships evolve into long-term emotional arcs.

- [ ] **Character Origin System**: Define 5 origin backgrounds (Foundry Orphan, Aristocratic Heir, Guild Apprentice, Smuggler's Ward, Automata Tinkerer). Each origin provides a unique starting location, 2 bonus items, a pre-seeded NPC relationship (+0.3 disposition with a specific NPC), and a personal quest hook woven into the character creation prompt.
- [ ] **NPC Relationship Arcs**: Extend the disposition system with relationship milestones. At disposition thresholds (0.3, 0.6, 0.9), NPCs unlock new dialogue branches — sharing secrets, offering exclusive quests, or proposing alliances. At -0.6, NPCs actively work against the player (reporting their location, raising prices, refusing service).
- [ ] **NPC-to-NPC Relationship Web**: Track `npc_relationships` as a separate table mapping pairs of NPCs to disposition values. The overheard dialogue system uses this web to generate gossip, alliances, and betrayals that the player can observe and influence.
