# D6 — Interactive World Map Polish Design

Roadmap item: **D6** (Technical Quality). `WorldMap.tsx` exists; complete the faction
territory overlay and the airship travel animation.

## Current state
- Airship travel: a plain green dot tweens along a straight line during travel — works but
  minimal. No dotted route, no altitude readout.
- Faction overlay: `NodeData.controllingFaction` exists but is never populated or drawn.
- `/state`'s `all_locations` already includes `faction_id` per location.

## Decisions (confirmed)
- Faction overlay = color nodes by controlling faction + an HTML legend. No WebSocket war
  animation or emblem art.
- Airship animation = dashed route line + an airship glyph + a progress/altitude readout.
  No weather FX.

## Pure helpers — `frontend/src/utils/worldMapUtils.ts`
```ts
export function factionColor(factionId?: string | null): string  // deterministic; neutral when empty
export function easeInOutQuad(t: number): number
export function travelPoint(from: {x,y}, to: {x,y}, progress: number): {x, y}
export function altitudeForProgress(progress: number, maxAltitude: number): number  // eased arc, 0 at ends
export function humanizeFactionId(id: string): string  // "iron_syndicate" -> "Iron Syndicate"
```
`factionColor` maps an id to a stable color from a fixed palette (hash → index); falsy id →
a neutral slate.

## `WorldMap.tsx` changes
- `Location` type (`api.ts`) gains `faction_id?: string | null`.
- Node memo sets `controllingFaction = loc.faction_id`; the node core uses
  `factionColor(controllingFaction)` when the node is neither current nor hovered.
- **Faction legend**: an HTML overlay (bottom-left) listing the distinct factions among the
  locations, each with a color swatch (`factionColor`) and `humanizeFactionId` label.
- **Travel**: during `travelState`, draw a dashed line from → to (`setLineDash`), an
  airship glyph (small hull shape) at `travelPoint(fromNode, toNode, progress)`, and an
  HTML readout showing `Math.round(progress*100)%` and the eased altitude
  (`altitudeForProgress`).

## Tests
- `frontend/src/__tests__/utils/worldMapUtils.test.ts`:
  - `factionColor`: same id → same color; different ids → (generally) different; empty →
    neutral constant.
  - `easeInOutQuad`: 0→0, 1→1, 0.5→0.5.
  - `travelPoint`: progress 0 → from, 1 → to, 0.5 → midpoint.
  - `altitudeForProgress`: 0 and 1 → 0; 0.5 → maxAltitude; within [0, maxAltitude].
  - `humanizeFactionId`: `"iron_syndicate"` → `"Iron Syndicate"`.
- `frontend/src/__tests__/components/WorldMap.test.tsx` (mock api):
  - renders without crashing (jsdom canvas `getContext` is null — already guarded),
  - the faction legend shows humanized faction names when locations carry `faction_id`.

## Out of scope
- Real-time faction-war recoloring, emblem images, weather/cloud/lightning FX, fuel-burn
  visuals, backend changes.

## Acceptance
- Location nodes are colored by controlling faction with a legend; airship travel shows a
  dashed route, a glyph, and a progress/altitude readout. Suites green; `tsc`/`oxlint` clean.
