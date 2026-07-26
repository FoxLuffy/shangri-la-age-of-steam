// Pure helpers for the interactive world map (roadmap D6).

export const NEUTRAL_COLOR = '#334155'; // slate-700

// Fixed, readable palette for faction territories.
const FACTION_PALETTE = [
  '#b91c1c', // red-700
  '#1d4ed8', // blue-700
  '#15803d', // green-700
  '#7e22ce', // purple-700
  '#b45309', // amber-700
  '#0e7490', // cyan-700
  '#be185d', // pink-700
  '#4d7c0f', // lime-700
];

function hashString(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (h * 31 + s.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

/** Deterministic color for a faction id; neutral when the id is empty. */
export function factionColor(factionId?: string | null): string {
  if (!factionId) return NEUTRAL_COLOR;
  return FACTION_PALETTE[hashString(factionId) % FACTION_PALETTE.length];
}

/** easeInOutQuad — 0 at t=0, 1 at t=1, symmetric around 0.5. */
export function easeInOutQuad(t: number): number {
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
}

export interface Point {
  x: number;
  y: number;
}

/** Linear interpolation between two points. */
export function travelPoint(from: Point, to: Point, progress: number): Point {
  return {
    x: from.x + (to.x - from.x) * progress,
    y: from.y + (to.y - from.y) * progress,
  };
}

/** Eased altitude arc: 0 at both ends, peaking at maxAltitude mid-journey. */
export function altitudeForProgress(progress: number, maxAltitude: number): number {
  const arc = Math.sin(Math.min(Math.max(progress, 0), 1) * Math.PI);
  return arc * maxAltitude;
}

/** "iron_syndicate" -> "Iron Syndicate". */
export function humanizeFactionId(id: string): string {
  return id
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}
