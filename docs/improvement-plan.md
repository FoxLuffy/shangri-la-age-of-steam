# Improvement Plan — post lengthy playtest (2026-07-27)

## Playtest findings (latest build)

Lengthy session on production (Scrapper / Smuggler's Ward). **The game now plays real** —
natural-language actions reliably drive mechanics.

### Working ✅
- **Combat**: `combat_updates` now fires — a fight **starts** (CombatSession + turn order)
  and **resolves** (`is_combat_active` false), with HP applied (took −10 → 90/100).
- **NPC dedup**: no duplicates across turns; genuinely new NPCs (Old Mallow, Hooded
  Figure) added correctly, existing ones not re-listed.
- **Inventory**: add **and** remove both land (Brass Skeleton Key added, then destroyed →
  gone from the pack).
- **Main quest (staged)**: advanced through **all 4 stages → completed** end-to-end; each
  objective-completing turn emitted `advance_stage`.
- Origin start location (CR9), coins, minigame trigger, narrative crafting, narrator
  leading (CR8) — all confirmed in this or the prior session.
- Two-pass state extraction is the backbone and is holding up. Latency ~6–10 s/turn.

### Issues found 🔧
1. **Combat opponent fidelity** (Medium). `apply_combat_update` builds combat participants
   from `world_state.active_npcs_ids` + players — so the fight I started against a narrated
   "Syndicate enforcer" listed **Kaelen Ironhand** (a scene-set NPC) as the opponent. The
   narrated antagonist isn't instantiated as a combatant.
   - Fix direction: when combat starts, instantiate the antagonist named in the narration
     (via the extractor's `active_npcs` / a `combat_updates.enemies` list) and use those as
     participants, not whoever happens to be in the scene set.
2. **NPC engagement / earshot** (Feature — see below). The LLM receives *all* present NPCs
   with no signal for **who the player is actually engaged with**. This muddies dialogue
   focus and is the basis for the requested feature.

---

## Feature: NPC earshot / active engagement

**Goal:** tell the LLM which active NPCs are **in earshot / engaged** (the player is
currently interacting with them) vs merely **present nearby** (background). This sharpens
dialogue focus ("who can hear and respond to me right now?") and downstream logic
(combat targeting, overheard gossip, disposition changes only for those addressed).

### Model
- Add `in_earshot: bool = False` to the `NPC` pydantic model (`backend/models.py`). It is a
  derived, per-request flag (not persisted on the DB NPC).
- Reuse the existing **`world_state.active_npcs_ids`** as the authoritative *engaged / in-
  earshot* set. It is already location-scoped (a scene NPC only surfaces when at the current
  location), so it is the natural home for "currently engaged".

### Engagement detection (when an NPC enters/leaves earshot)
1. **Enter** — an NPC becomes in-earshot when:
   - the player's action **names** a present NPC (substring match on the NPC's name), or
   - the engine/extractor emits them in `active_npcs` (the LLM introduced/addressed them),
   - → add their id to `active_npcs_ids`.
2. **Leave** — clear/prune earshot when the player **travels** (location change): reset
   `active_npcs_ids` so you are no longer "in conversation" with anyone at the old place.
   Optionally decay: drop an NPC from the set after N turns without being addressed.

### Surfacing
- `get_latest_state`: set `in_earshot = (npc.id in active_npcs_ids)` on each active NPC.
  NPCs at the location but not in the set → `in_earshot: False` (background presence).
- `narrative_prompt.j2`: split the NPC block into **"In earshot (engaged)"** and **"Also
  present nearby"**, and instruct: *only in-earshot NPCs can directly hear and respond;
  background NPCs may be observed or overheard but are not in conversation.*
- `_extract_state` prompt: pass the in-earshot names, and bias dialogue/disposition/quest
  updates toward the engaged NPC(s).
- Frontend (optional): the Environment overview marks engaged NPCs (e.g. a "listening" dot)
  vs background.

### Phasing
- **P1 (DONE, #179):** `in_earshot` field + derivation in `get_latest_state`;
  engagement-on-name-mention; clear-on-travel. Prompt split. Tests: name-mention marks
  in-earshot; travel clears; background NPC has `in_earshot: False`.
- **P2 (DONE, #180):** `_extract_state` splits engaged vs nearby NPCs and hints combat
  targeting toward the engaged NPC; **focus-shift decay** — naming a different NPC moves
  focus to them and drops the previously-engaged to nearby.
- **P3 (DONE, #180):** Active NPCs panel splits into "In earshot — actively engaged"
  (highlighted) vs "Nearby" (dimmed) groups.

### Acceptance
- Addressing an NPC by name marks them `in_earshot: True`; unaddressed present NPCs are
  `in_earshot: False`; travelling clears engagement. The prompt distinguishes engaged vs
  background, and the narrator responds only for engaged NPCs.

---

## Prioritized backlog
1. **Earshot P1** (#179) — DONE. Dialogue focus + combat targeting foundation.
2. **Combat opponent fidelity** (#179) — DONE. Narrated antagonist instantiated as combatant.
3. **Earshot P2/P3** (#180) — DONE. Extractor split + focus-shift decay + frontend groups.

All planned items shipped.

## Verified test baseline
Backend 160, frontend 107 (green). Two-pass state extraction + all prior playtest fixes
(inventory remove, NPC dedup, combat trigger) merged (#175–#177).
